import cv2
import time
import pickle
import yaml
import numpy as np
from datetime import datetime
from src.camera.webcam_camera import cameraDroneThread
from src.recognition.recognizer import Models
from src.ui.display import UI
from src.spoof.antispoof import MiniFASNetV2
from src.database.database import EmbeddingDatabase

def main():
    # Load configuration
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("[ERROR] config.yaml not found. Please create configuration file.")
        exit(1)
    except yaml.YAMLError as e:
        print(f"[ERROR] Invalid YAML in config.yaml: {e}")
        exit(1)

    # Initialize camera based on config
    if config["camera"]["type"] == "webcam":
        camera = cameraDroneThread(config["camera"]["source"]).start()
    else:
        camera = cameraDroneThread(config["camera"]["rtsp_url"]).start()
    
    models = Models()

    # Call liveness module
    liveness = MiniFASNetV2()

    # Load Database based on configuration mode
    db_mode = config["database"].get("mode", "legacy")
    
    if db_mode == "multiple":
        # NEW: Multiple embedding database
        print("[INFO] Loading multiple embedding database...")
        embeddings_db = EmbeddingDatabase(config["database"]["embeddings_dir"])
        embeddings_db.load()
        
        if embeddings_db.get_total_embedding_count() == 0:
            print("[ERROR] Multiple embedding database is empty.")
            print("[ERROR] Please perform enrollment before running recognition.")
            exit(1)
        
        print(f"[INFO] Loaded {embeddings_db.get_total_embedding_count()} embeddings from {len(embeddings_db.get_person_names())} identities")
        database_mode = "multiple"
    else:
        # LEGACY: Single pickle database
        print("[INFO] Loading legacy face database...")
        try:
            with open(config["database"]["path"], "rb") as f:
                face_db = pickle.load(f)
            print(f"[INFO] Loaded {len(face_db)} faces from database.")
            database_mode = "legacy"
        except Exception as e:
            print(f"[ERROR] Failed to load legacy database: {e}")
            exit(1)
    
    # Configure Performance Variables from config
    SIMILARITY_THRESHOLD = config["recognition"]["similarity_threshold"]
    frame_skip_rate = config["processing"]["frame_skip"]
    fps_smoothing = config["processing"]["fps_smoothing"]
    
    # Performance measurement variables
    recognition_latencies = []
    embedding_comparisons = 0
    total_recognitions = 0
    accepted_recognitions = 0
    unknown_recognitions = 0
    spoof_detections = 0
    
    # Pipeline timing metrics
    camera_times = []
    detection_times = []
    recognition_times = []
    minifasnet_times = []
    ui_times = []
    total_frame_times = []
    
    # FPS counters
    camera_fps_values = []
    display_fps_values = []
    recognition_fps_values = []
    
    # Initialize state variables
    frame_count = 0
    recognition_count = 0
    fps_smoothed = 0
    prev_time = time.time()
    prev_display_time = time.time()
    prev_recognition_time = time.time()
    
    # Saving Temporary face
    last_detected_faces = []
    is_under_attack = False
    attack_cooldown = 0
    ema_liveness_score = 0.0  # EMA for liveness score

    print("[INFO] Running...")

    # Initialize UI
    app_instance = UI()

    cv2.namedWindow("Drone E99 Face Recognition and Anti Spoofing")

    while True:
        frame = camera.read()
        
        if frame is None:
            continue

        if frame_count % (frame_skip_rate + 1) == 0:
            faces = models.detect_and_recognize(frame)
            
            # Reset previous faces
            last_detected_faces = []

            is_under_attack = False
            
            # Take note of detected faces for drawing
            rec_start_time = time.time()
            
            for face in faces:
                bbox = face.bbox.astype(int)
                query_feat = face.embedding / np.linalg.norm(face.embedding)

                max_sim = 0.0
                identity = "Unknown"
                comparisons = 0
                
                if database_mode == "multiple":
                    # NEW: Multiple embeddings per identity - MAX similarity
                    for person_name, person_embeddings in embeddings_db.get_all_embeddings().items():
                        for person_emb in person_embeddings:
                            sim = np.dot(query_feat, person_emb)
                            comparisons += 1
                            if sim > max_sim:
                                max_sim = sim
                                identity = person_name
                else:
                    # LEGACY: Single embedding per identity
                    for name, db_feat in face_db.items():
                        sim = np.dot(query_feat, db_feat)
                        comparisons += 1
                        if sim > max_sim:
                            max_sim = sim
                            identity = name
                
                # Record metrics
                embedding_comparisons += comparisons
                total_recognitions += 1
                
                # Compare with database
                if max_sim >= SIMILARITY_THRESHOLD:
                    display_name = f"{identity} ({max_sim:.2f})"
                    id_color = (0, 255, 0)
                    correct_recognitions += 1  # Assume correct if above threshold
                else:
                    display_name = f"Unknown ({max_sim:.2f})"
                    id_color = (0, 255, 255)
                
                # Record latency
                rec_latency = time.time() - rec_start_time
                recognition_latencies.append(rec_latency)

                # Liveness Check
                is_real, liveness_score = liveness.check_liveness(frame, bbox)
                if is_real:
                    liveness_label = "Real"
                    color = (0, 255, 0)
                else:
                    liveness_label = "Spoof"
                    color = (0, 0, 255)
                    is_under_attack = True

                last_detected_faces.append((bbox, display_name, liveness_label, liveness_score,id_color, color))

        # Make Bounding Box and lable
        for bbox, display_name, liveness_label, liveness_score, id_color, color in last_detected_faces:
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), id_color, 2)
            cv2.putText(frame, display_name, (bbox[0], bbox[1] - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, id_color, 2)
            cv2.putText(frame, f"{liveness_label} ({liveness_score:.2f})", (bbox[0], bbox[1] -5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Display timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, current_time, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Count FPS
        time_diff = time.time() - prev_time
        if time_diff > 0:
            fps_smoothed = (fps_smoothed * fps_smoothing) + ((1 / time_diff) * (1 - fps_smoothing)) if fps_smoothed > 0 else (1 / time_diff)
        prev_time = time.time()
        
        # Display FPS
        cv2.putText(frame, f"FPS: {int(fps_smoothed)}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        frame_count += 1

        frame = app_instance.process_ui(frame)

        # Show App
        cv2.imshow("Drone E99 Face Recognition and Anti Spoofing", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('s'):
            app_instance.take_snapshot(frame)
        elif key == ord('r'):
            app_instance.toggle_recording()

    # Print performance summary before exit
    print('')
    print('=' * 70)
    print('PERFORMANCE SUMMARY')
    print('=' * 70)
    print(f'Database Mode: {database_mode}')
    print(f'Total Frames Processed: {frame_count}')
    print(f'Total Recognitions: {total_recognitions}')
    
    if total_recognitions > 0:
        avg_latency = sum(recognition_latencies) / len(recognition_latencies) if recognition_latencies else 0
        avg_comparisons = embedding_comparisons / total_recognitions
        accuracy = correct_recognitions / total_recognitions * 100
        
        print(f'Average Recognition Latency: {avg_latency*1000:.2f}ms')
        print(f'Average Embedding Comparisons: {avg_comparisons:.1f}')
        print(f'Recognition Accuracy: {accuracy:.1f}%')
        print(f'Average FPS: {fps_smoothed:.1f}')
    
    print('=' * 70)
    print('')

    camera.stop()
    app_instance.cleanup()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()