import sys
import cv2
import time
import pickle
import yaml
import signal
import numpy as np
from datetime import datetime
from src.recognition.recognizer import Models
from src.ui.display import UI
from src.spoof.antispoof import MiniFASNetV2
from src.database.database import EmbeddingDatabase
from src.utils import _setup_cuda_paths


def _load_config():
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("[ERROR] config.yaml not found.")
        exit(1)
    except yaml.YAMLError as e:
        print(f"[ERROR] Invalid YAML in config.yaml: {e}")
        exit(1)

    required_sections = ["camera", "recognition", "spoofing", "processing", "database"]
    for section in required_sections:
        if section not in config:
            print(f"[ERROR] Missing config section: '{section}'")
            exit(1)

    if config["camera"]["type"] == "webcam" and not isinstance(config["camera"].get("source"), int):
        print("[ERROR] config: camera.source must be an integer for webcam type")
        exit(1)
    if config["camera"]["type"] == "drone" and not isinstance(config["camera"].get("rtsp_url"), str):
        print("[ERROR] config: camera.rtsp_url must be a string for drone type")
        exit(1)
    if not isinstance(config["recognition"].get("similarity_threshold"), (int, float)):
        print("[ERROR] config: recognition.similarity_threshold must be a number")
        exit(1)
    if not isinstance(config["processing"].get("frame_skip"), int):
        print("[ERROR] config: processing.frame_skip must be an integer")
        exit(1)

    return config


def init_components(config):
    provider = config.get("processing", {}).get("provider", "cuda")
    if provider == "cuda":
        _setup_cuda_paths()

    if config["camera"]["type"] == "webcam":
        from src.camera.webcam_camera import cameraDroneThread
        camera = cameraDroneThread(config["camera"]["source"]).start()
    else:
        from src.camera.rtsp_camera import cameraDroneThread
        camera = cameraDroneThread(config["camera"]["rtsp_url"]).start()

    models = Models(provider=provider, model_name=config["recognition"]["model_name"],
                    det_size=tuple(config["recognition"]["det_size"]))
    liveness = MiniFASNetV2(provider=provider,
                            liveness_threshold=config["spoofing"]["liveness_threshold"])

    db_mode = config["database"].get("mode", "legacy")
    if db_mode == "multiple":
        print("[INFO] Loading multiple embedding database...")
        embeddings_db = EmbeddingDatabase(config["database"]["embeddings_dir"])
        embeddings_db.load()
        if embeddings_db.get_total_embedding_count() == 0:
            print("[ERROR] Multiple embedding database is empty.")
            print("[ERROR] Please perform enrollment before running recognition.")
            exit(1)
        print(f"[INFO] Loaded {embeddings_db.get_total_embedding_count()} embeddings "
              f"from {len(embeddings_db.get_person_names())} identities")
        return camera, models, liveness, embeddings_db, None, "multiple"
    else:
        print("[INFO] Loading legacy face database...")
        try:
            with open(config["database"]["path"], "rb") as f:
                face_db = pickle.load(f)
            print(f"[INFO] Loaded {len(face_db)} faces from database.")
            return camera, models, liveness, None, face_db, "legacy"
        except Exception as e:
            print(f"[ERROR] Failed to load legacy database: {e}")
            exit(1)


def print_summary(detection_times, total_pipeline_times,
                  total_recognitions, accepted_recognitions,
                  spoof_detections):
    print('')
    print('=' * 50)
    print('PERFORMANCE SUMMARY')
    print('=' * 50)

    if total_pipeline_times:
        avg_ms = sum(total_pipeline_times) / len(total_pipeline_times) * 1000
        fps = 1000.0 / avg_ms if avg_ms > 0 else 0
        print(f'  FPS:                    {fps:.1f}')

    if detection_times:
        avg_det = sum(detection_times) / len(detection_times) * 1000
        print(f'  Detection Latency:      {avg_det:.1f} ms')

    if total_recognitions > 0:
        acc = accepted_recognitions / total_recognitions * 100
        print(f'  Recognition Accuracy:   {acc:.1f}%  ({accepted_recognitions}/{total_recognitions})')

    print(f'  Spoof Detections:       {spoof_detections}')
    print('=' * 50)
    print('')


_cleanup_components = None


def _signal_handler(sig, frame):
    print("\n[INFO] Shutdown requested...")
    if _cleanup_components:
        camera, app_instance, headless = _cleanup_components
        if not headless:
            cv2.destroyAllWindows()
        app_instance.cleanup()
        camera.stop()
    sys.exit(0)


def main():
    global _cleanup_components
    signal.signal(signal.SIGINT, _signal_handler)

    config = _load_config()
    camera, models, liveness, embeddings_db, face_db, database_mode = init_components(config)

    SIMILARITY_THRESHOLD = config["recognition"]["similarity_threshold"]
    frame_skip_rate = config["processing"]["frame_skip"]
    fps_smoothing = config["processing"]["fps_smoothing"]
    headless = config.get("processing", {}).get("headless", False)

    total_recognitions = 0
    accepted_recognitions = 0
    spoof_detections = 0

    detection_times = []
    total_pipeline_times = []

    frame_count = 0
    effective_fps = 0.0
    last_detected_faces = []
    ema_liveness_score = 0.0

    print("[INFO] Running...")
    app_instance = UI()
    _cleanup_components = (camera, app_instance, headless)
    if not headless:
        cv2.namedWindow("Drone E99 Face Recognition and Anti Spoofing")

    while True:
        frame_start = time.time()
        frame = camera.read()
        if frame is None:
            continue

        frame_count += 1

        if frame_count % (frame_skip_rate + 1) == 0:
            t = time.time()
            faces = models.detect_and_recognize(frame)
            detection_times.append(time.time() - t)

            last_detected_faces = []

            for face in faces:
                bbox = face.bbox.astype(int)
                query_feat = face.embedding / np.linalg.norm(face.embedding)

                max_sim = 0.0
                identity = "Unknown"

                if database_mode == "multiple":
                    for person_name, person_embeddings in embeddings_db.get_all_embeddings().items():
                        for person_emb in person_embeddings:
                            sim = np.dot(query_feat, person_emb)
                            if sim > max_sim:
                                max_sim = sim
                                identity = person_name
                else:
                    for name, db_feat in face_db.items():
                        sim = np.dot(query_feat, db_feat)
                        if sim > max_sim:
                            max_sim = sim
                            identity = name

                total_recognitions += 1

                if max_sim >= SIMILARITY_THRESHOLD:
                    display_name = f"{identity} ({max_sim:.2f})"
                    id_color = (0, 255, 0)
                    accepted_recognitions += 1
                else:
                    display_name = f"Unknown ({max_sim:.2f})"
                    id_color = (0, 255, 255)

                is_real, raw_liveness_score = liveness.check_liveness(frame, bbox)

                ema_alpha = 0.3
                ema_liveness_score = (ema_alpha * raw_liveness_score) + ((1 - ema_alpha) * ema_liveness_score)
                liveness_label = "Real" if is_real else "Spoof"
                color = (0, 255, 0) if is_real else (0, 0, 255)
                if not is_real:
                    spoof_detections += 1

                last_detected_faces.append((bbox, display_name, liveness_label,
                                            raw_liveness_score, ema_liveness_score, id_color, color))

        ui_start = time.time()
        for bbox, display_name, liveness_label, raw_score, ema_score, id_color, color in last_detected_faces:
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), id_color, 2)
            cv2.putText(frame, display_name, (bbox[0], bbox[1] - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, id_color, 2)
            cv2.putText(frame, f"{liveness_label} ({raw_score:.2f})", (bbox[0], bbox[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.putText(frame, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        frame = app_instance.process_ui(frame)

        ui_time = time.time() - ui_start

        if frame_count % (frame_skip_rate + 1) == 0:
            total_pipeline_times.append(time.time() - frame_start)

        if total_pipeline_times:
            avg = sum(total_pipeline_times) / len(total_pipeline_times)
            if avg > 0:
                effective_fps = (fps_smoothing * effective_fps) + ((1 - fps_smoothing) * (1.0 / avg))

        cv2.putText(frame, f"FPS: {int(effective_fps)}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        if not headless:
            cv2.imshow("Drone E99 Face Recognition and Anti Spoofing", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                app_instance.take_snapshot(frame)
            elif key == ord('r'):
                app_instance.toggle_recording()
        else:
            time.sleep(0.001)

    print_summary(detection_times, total_pipeline_times,
                  total_recognitions, accepted_recognitions,
                  spoof_detections)

    camera.stop()
    app_instance.cleanup()
    if not headless:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()