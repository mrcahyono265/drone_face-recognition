import sys
import os
import cv2
import time
import pickle
import signal
import csv
import numpy as np
from datetime import datetime
from src.recognition.recognizer import Models
from src.ui.display import UI
from src.spoof.antispoof import MiniFASNetV2
from src.database.database import EmbeddingDatabase
from src.utils import _setup_cuda_paths, load_config


def _load_config():
    config = load_config()

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
    if config["camera"]["type"] == "video" and not isinstance(config["camera"].get("video_dir"), str):
        print("[ERROR] config: camera.video_dir must be a string for video type")
        exit(1)
    if not isinstance(config["recognition"].get("similarity_threshold"), (int, float)):
        print("[ERROR] config: recognition.similarity_threshold must be a number")
        exit(1)
    if type(config["processing"].get("frame_skip")) is not int:
        print("[ERROR] config: processing.frame_skip must be an integer")
        exit(1)

    return config


def init_components(config):
    provider = config.get("processing", {}).get("provider", "cuda")
    if provider == "cuda":
        _setup_cuda_paths()

    if config["camera"]["type"] == "webcam":
        from src.camera.webcam_camera import WebcamStream
        camera = WebcamStream(config["camera"]["source"]).start()
    elif config["camera"]["type"] == "video":
        from src.camera.video_camera import VideoStream
        camera = VideoStream(config["camera"]["video_dir"]).start()
    else:
        from src.camera.rtsp_camera import RTSPStream
        camera = RTSPStream(config["camera"]["rtsp_url"]).start()

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


_cleanup_components = None


def _signal_handler(sig, frame):
    print("\n[INFO] Shutdown requested...")
    if _cleanup_components:
        camera, app_instance, headless, debug_file = _cleanup_components
        if not headless:
            cv2.destroyAllWindows()
        app_instance.cleanup()
        camera.stop()
        if debug_file:
            debug_file.close()
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
    camera_type = config["camera"]["type"]
    output_dir = config.get("output", {}).get("video_dir", "inference_output")

    debug_enabled = config.get("debug", {}).get("csv_enabled", False)
    debug_file = None
    debug_writer = None
    if debug_enabled:
        debug_path = config.get("debug", {}).get("csv_path", "reports/debug_latest.csv")
        os.makedirs("reports", exist_ok=True)
        debug_file = open(debug_path, "w", newline="")
        debug_writer = csv.writer(debug_file)
        debug_writer.writerow(["timestamp", "identity", "similarity",
                               "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2",
                               "liveness_score", "liveness_label"])

    detection_sum = 0.0
    detection_count = 0
    pipeline_sum = 0.0
    pipeline_count = 0

    frame_count = 0
    effective_fps = 0.0
    last_detected_faces = []
    identity_stats = {}
    is_video_mode = camera_type == "video"
    prev_video_name = None

    print("[INFO] Running...")
    app_instance = UI(output_dir=output_dir, source_prefix=camera_type)
    _cleanup_components = (camera, app_instance, headless, debug_file)
    if not headless:
        cv2.namedWindow("Drone E99 Face Recognition and Anti Spoofing")

    while True:
        t0 = time.time()
        frame = camera.read()

        if frame is None:
            if is_video_mode and getattr(camera, 'exhausted', False):
                break
            continue

        frame_count += 1
        now = datetime.now()

        if frame_count % (frame_skip_rate + 1) == 0:
            faces = models.detect_and_recognize(frame)
            detection_sum += time.time() - t0
            detection_count += 1

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

                if max_sim >= SIMILARITY_THRESHOLD:
                    display_name = f"{identity} ({max_sim:.2f})"
                    id_color = (0, 255, 0)
                else:
                    identity = "Unknown"
                    display_name = f"Unknown ({max_sim:.2f})"
                    id_color = (0, 255, 255)

                c, s = identity_stats.get(identity, (0, 0.0))
                identity_stats[identity] = (c + 1, s + max_sim)

                is_real, raw_liveness_score = liveness.check_liveness(frame, bbox)

                liveness_label = "Real" if is_real else "Spoof"
                color = (0, 255, 0) if is_real else (0, 0, 255)

                if debug_writer:
                    debug_writer.writerow([now.isoformat(), identity, f"{max_sim:.3f}",
                                           bbox[0], bbox[1], bbox[2], bbox[3],
                                           f"{raw_liveness_score:.3f}", liveness_label])

                last_detected_faces.append((bbox, display_name, liveness_label,
                                            max_sim, raw_liveness_score, id_color, color))

        for bbox, display_name, liveness_label, _, raw_score, id_color, color in last_detected_faces:
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), id_color, 2)
            cv2.putText(frame, display_name, (bbox[0], bbox[1] - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, id_color, 2)
            cv2.putText(frame, f"{liveness_label} ({raw_score:.2f})", (bbox[0], bbox[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.putText(frame, now.strftime("%Y-%m-%d %H:%M:%S"), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Auto-record for video mode: detect video file change (BEFORE process_ui)
        if is_video_mode:
            current_video_name = getattr(camera, 'current_video_name', None)
            if current_video_name != prev_video_name:
                if app_instance.is_recording:
                    app_instance.stop_recording()
                video_name_noext = os.path.splitext(current_video_name)[0]
                ts = now.strftime("%Y%m%d_%H%M%S")
                record_filename = os.path.join(output_dir, f"video_{video_name_noext}_{ts}.avi")
                h, w = frame.shape[:2]
                app_instance.frame_h, app_instance.frame_w = h, w
                app_instance.start_recording(record_filename)
                prev_video_name = current_video_name

        frame = app_instance.process_ui(frame)

        pipeline_dt = time.time() - t0
        pipeline_sum += pipeline_dt
        pipeline_count += 1

        if pipeline_count > 0:
            avg = pipeline_sum / pipeline_count
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
            time.sleep(0.01)

    # Stop recording if still active (video mode auto-record)
    if app_instance.is_recording:
        app_instance.stop_recording()

    print('')
    print('=' * 50)
    print('SUMMARY')
    print('=' * 50)

    prov = config.get("processing", {}).get("provider", "cuda")
    print(f'  Provider:               {prov}')

    if pipeline_count > 0:
        avg_ms = pipeline_sum / pipeline_count * 1000
        fps = 1000.0 / avg_ms if avg_ms > 0 else 0
        print(f'  FPS:                    {fps:.1f}')

    if detection_count > 0:
        avg_det = detection_sum / detection_count * 1000
        print(f'  Detection Latency:      {avg_det:.1f} ms')

    if identity_stats:
        print('---')
        for name, (c, s) in sorted(identity_stats.items()):
            avg = s / c
            print(f'  {name:<20} {avg:.2f} avg ({c}x)')

    print('=' * 50)
    print('')

    camera.stop()
    if debug_file:
        debug_file.close()
    app_instance.cleanup()
    if not headless:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()