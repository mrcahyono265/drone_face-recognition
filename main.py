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
    embedding_comparisons = 0
    total_recognitions = 0
    accepted_recognitions = 0
    unknown_recognitions = 0
    spoof_detections = 0
    
    # Pipeline timing metrics (processing only, excludes async camera capture)
    detection_times = []
    recognition_times = []
    minifasnet_times = []
    ui_times = []
    total_pipeline_times = []
    
    # FPS counters
    camera_fps_values = []
    
    # Initialize state variables
    frame_count = 0
    recognition_count = 0
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
        frame_start_time = time.time()
        
        # Stage 1: Camera Capture (asynchronous - just read from buffer)
        frame = camera.read()
        
        if frame is None:
            continue
        
        frame_count += 1
        
        # Stage 2-5: Processing (only on recognition frames)
        if frame_count % (frame_skip_rate + 1) == 0:
            # Stage 2: Face Detection
            detection_start = time.time()
            faces = models.detect_and_recognize(frame)
            detection_time = time.time() - detection_start
            detection_times.append(detection_time)
            
            # Reset previous faces
            last_detected_faces = []

            is_under_attack = False
            recognition_count += 1
            
            # Take note of detected faces for drawing
            for face in faces:
                bbox = face.bbox.astype(int)
                query_feat = face.embedding / np.linalg.norm(face.embedding)

                max_sim = 0.0
                identity = "Unknown"
                comparisons = 0
                
                # Stage 3: Face Recognition (Embedding Comparison)
                recognition_compare_start = time.time()
                
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
                
                recognition_compare_time = time.time() - recognition_compare_start
                recognition_times.append(recognition_compare_time)
                
                # Record metrics
                embedding_comparisons += comparisons
                total_recognitions += 1
                
                # Compare with database
                if max_sim >= SIMILARITY_THRESHOLD:
                    display_name = f"{identity} ({max_sim:.2f})"
                    id_color = (0, 255, 0)
                    accepted_recognitions += 1
                else:
                    display_name = f"Unknown ({max_sim:.2f})"
                    id_color = (0, 255, 255)
                    unknown_recognitions += 1

                # Stage 4: MiniFASNet Anti-Spoofing
                minifasnet_start = time.time()
                is_real, raw_liveness_score = liveness.check_liveness(frame, bbox)
                minifasnet_time = time.time() - minifasnet_start
                minifasnet_times.append(minifasnet_time)
                
                # Apply EMA smoothing to liveness score
                ema_alpha = 0.3  # EMA smoothing factor
                ema_liveness_score = (ema_alpha * raw_liveness_score) + ((1 - ema_alpha) * ema_liveness_score)
                
                if is_real:
                    liveness_label = "Real"
                    color = (0, 255, 0)
                else:
                    liveness_label = "Spoof"
                    color = (0, 0, 255)
                    spoof_detections += 1

                last_detected_faces.append((bbox, display_name, liveness_label, raw_liveness_score, ema_liveness_score, id_color, color))

        # Stage 5: UI Rendering (COMPLETE - includes all UI operations)
        ui_start = time.time()
        
        # Make Bounding Box and label
        for bbox, display_name, liveness_label, raw_score, ema_score, id_color, color in last_detected_faces:
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), id_color, 2)
            cv2.putText(frame, display_name, (bbox[0], bbox[1] - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, id_color, 2)
            cv2.putText(frame, f"{liveness_label} ({raw_score:.2f})", (bbox[0], bbox[1] -5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Display timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, current_time, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        frame = app_instance.process_ui(frame)
        
        # Show App
        cv2.imshow("Drone E99 Face Recognition and Anti Spoofing", frame)
        key = cv2.waitKey(1) & 0xFF
        
        # UI time INCLUDES: drawing + process_ui() + imshow() + waitKey()
        ui_time = time.time() - ui_start
        ui_times.append(ui_time)
        
        # Total Pipeline Time (processing only, excludes async camera capture)
        # Measures: Detection (if run) + Recognition + MiniFASNet + UI
        # For non-recognition frames: only UI time
        if frame_count % (frame_skip_rate + 1) == 0:
            # Recognition frame: measure all stages
            pipeline_time = time.time() - frame_start_time
        else:
            # Non-recognition frame: only UI time
            pipeline_time = ui_time
        
        total_pipeline_times.append(pipeline_time)

        if key == ord('q'):
            break
        elif key == ord('s'):
            app_instance.take_snapshot(frame)
        elif key == ord('r'):
            app_instance.toggle_recording()

    # Print performance summary before exit
    print('')
    print('=' * 70)
    print('PIPELINE PERFORMANCE SUMMARY')
    print('=' * 70)
    print(f'Database Mode: {database_mode}')
    print(f'Total Frames Processed: {frame_count}')
    print(f'Total Recognition Events: {recognition_count}')
    print('')
    
    print('PROCESSING STAGE TIMING:')
    print('-' * 70)
    print('  (All times measured per execution, not averaged per frame)')
    print('')
    
    if detection_times:
        avg_detection = sum(detection_times)/len(detection_times) * 1000
        print(f'  1. Face Detection:        {avg_detection:.2f} ms (avg per inference)')
    
    if recognition_times:
        avg_recognition = sum(recognition_times)/len(recognition_times) * 1000
        print(f'  2. Recognition (compare):   {avg_recognition:.2f} ms (avg per face)')
    
    if minifasnet_times:
        avg_minifasnet = sum(minifasnet_times)/len(minifasnet_times) * 1000
        print(f'  3. MiniFASNet V2:         {avg_minifasnet:.2f} ms (avg per face)')
    
    if ui_times:
        avg_ui = sum(ui_times)/len(ui_times) * 1000
        print(f'  4. UI Rendering:          {avg_ui:.2f} ms (avg per frame)')
        print(f'     (includes: drawing + process_ui + imshow + waitKey)')
    
    print('')
    
    if total_pipeline_times:
        avg_pipeline = sum(total_pipeline_times)/len(total_pipeline_times) * 1000
        effective_fps = 1000.0 / avg_pipeline if avg_pipeline > 0 else 0
        
        print(f'  TOTAL Pipeline:           {avg_pipeline:.2f} ms (avg per frame)')
        print(f'  Effective Processing FPS: {effective_fps:.2f} FPS')
        print('')
        
        # Validation: check if total is consistent with sum of stages
        # For recognition frames: total ≈ detection + recognition + minifasnet + ui
        # For non-recognition frames: total ≈ ui only
        # This is a rough estimate since detection runs every N frames
        recognition_frames = len(detection_times)
        non_recognition_frames = frame_count - recognition_frames
        
        if recognition_frames > 0 and non_recognition_frames > 0:
            expected_total = (
                (avg_detection * recognition_frames) +
                (avg_recognition * recognition_frames * 1.0) +  # assume 1 face avg
                (avg_minifasnet * recognition_frames * 1.0) +
                (avg_ui * frame_count)
            ) / frame_count
            
            print(f'  [Validation]')
            print(f'    Recognition frames: {recognition_frames}')
            print(f'    Non-recognition frames: {non_recognition_frames}')
            print(f'    Expected total (estimate): ~{expected_total:.2f} ms')
            print(f'    Measured total: {avg_pipeline:.2f} ms')
            
            if abs(expected_total - avg_pipeline) < avg_pipeline * 0.2:  # 20% tolerance
                print(f'    Status: ✓ CONSISTENT (within 20% tolerance)')
            else:
                print(f'    Status: ⚠ DISCREPANCY DETECTED')
                print(f'    Note: Total includes all processing overhead, not just stage times')
    
    print('')
    print('FPS METRICS:')
    print('-' * 70)
    
    # Calculate camera FPS from frame count and total time
    # This is the actual throughput of the camera thread
    if camera_fps_values:
        # Camera FPS is measured separately, just show info
        print(f'  Note: Camera capture is asynchronous (threaded)')
        print(f'        Camera FPS not included in pipeline timing')
    
    print('')
    print('RECOGNITION METRICS:')
    print('-' * 70)
    if total_recognitions > 0:
        # Calculate recognition rate (recognitions per second)
        total_runtime = sum(total_pipeline_times)  # Approximate total runtime
        recognition_rate = recognition_count / total_runtime if total_runtime > 0 else 0
        
        print(f'  Total Recognitions:     {total_recognitions}')
        print(f'  Accepted (>threshold):  {accepted_recognitions} ({accepted_recognitions/total_recognitions*100:.1f}%)')
        print(f'  Unknown (<threshold):   {unknown_recognitions} ({unknown_recognitions/total_recognitions*100:.1f}%)')
        print(f'  Avg Comparisons:        {embedding_comparisons/total_recognitions:.1f}')
        print(f'  Recognition Rate:       {recognition_rate:.2f} recognitions/sec')
    print('')
    
    print('ANTI-SPOOFING METRICS:')
    print('-' * 70)
    print(f'  Spoof Detections:  {spoof_detections}')
    print(f'  EMA Alpha:         0.3')
    print('')
    
    print('=' * 70)
    print('')

    camera.stop()
    app_instance.cleanup()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()