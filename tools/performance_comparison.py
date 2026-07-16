import cv2
import yaml
import time
import pickle
import numpy as np
from datetime import datetime
from src.camera.webcam_camera import WebcamStream
from src.recognition.recognizer import Models
from src.spoof.antispoof import MiniFASNetV2
from src.database.database import EmbeddingDatabase


def run_comparison_test(database_mode, num_frames=100):
    """
    Run performance comparison test for a specific database mode.
    
    Args:
        database_mode: "legacy" or "multiple"
        num_frames: Number of frames to test
    
    Returns:
        Dictionary with performance metrics
    """
    
    print('=' * 70)
    print(f'PERFORMANCE TEST: {database_mode.upper()} MODE')
    print('=' * 70)
    print('')
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize components
    camera = WebcamStream(config['camera']['source']).start()
    models = Models()
    liveness = MiniFASNetV2()
    
    # Load database based on mode
    if database_mode == 'multiple':
        print('Loading multiple embedding database...')
        embeddings_db = EmbeddingDatabase(config['database']['embeddings_dir'])
        embeddings_db.load()
        
        if embeddings_db.get_total_embedding_count() == 0:
            print('ERROR: Multiple embedding database is empty')
            return None
        
        print(f'Loaded {embeddings_db.get_total_embedding_count()} embeddings')
    else:
        print('Loading legacy database...')
        with open(config['database']['path'], 'rb') as f:
            face_db = pickle.load(f)
        print(f'Loaded {len(face_db)} identities')
    
    print('')
    print(f'Testing with {num_frames} frames...')
    print('')
    
    # Performance metrics
    latencies = []
    total_comparisons = 0
    total_recognitions = 0
    fps_values = []
    
    SIMILARITY_THRESHOLD = config['recognition']['similarity_threshold']
    frame_skip_rate = config['processing']['frame_skip']
    
    prev_time = time.time()
    frame_count = 0
    start_time = time.time()
    
    while frame_count < num_frames:
        frame = camera.read()
        
        if frame is None:
            continue
        
        if frame_count % (frame_skip_rate + 1) == 0:
            rec_start = time.time()
            
            faces = models.detect_and_recognize(frame)
            comparisons = 0
            
            for face in faces:
                query_feat = face.embedding / np.linalg.norm(face.embedding)
                max_sim = 0.0
                
                if database_mode == 'multiple':
                    for person_name, person_embeddings in embeddings_db.get_all_embeddings().items():
                        for person_emb in person_embeddings:
                            sim = np.dot(query_feat, person_emb)
                            comparisons += 1
                            if sim > max_sim:
                                max_sim = sim
                else:
                    for name, db_feat in face_db.items():
                        sim = np.dot(query_feat, db_feat)
                        comparisons += 1
                        if sim > max_sim:
                            max_sim = sim
                
                total_recognitions += 1
            
            latency = time.time() - rec_start
            latencies.append(latency)
            total_comparisons += comparisons
            
            # FPS calculation
            current_fps = 1.0 / (time.time() - prev_time) if time.time() - prev_time > 0 else 0
            fps_values.append(current_fps)
            prev_time = time.time()
        
        frame_count += 1
    
    total_time = time.time() - start_time
    camera.stop()
    
    # Calculate metrics
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    avg_comparisons = total_comparisons / total_recognitions if total_recognitions > 0 else 0
    avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0
    
    results = {
        'mode': database_mode,
        'total_frames': num_frames,
        'total_time': total_time,
        'total_recognitions': total_recognitions,
        'avg_latency_ms': avg_latency * 1000,
        'avg_comparisons': avg_comparisons,
        'avg_fps': avg_fps,
        'fps_std': np.std(fps_values) if fps_values else 0
    }
    
    # Print results
    print('')
    print('RESULTS:')
    print(f'  Total Time: {total_time:.2f}s')
    print(f'  Total Recognitions: {total_recognitions}')
    print(f'  Average Latency: {avg_latency*1000:.2f}ms')
    print(f'  Average Comparisons: {avg_comparisons:.1f}')
    print(f'  Average FPS: {avg_fps:.1f} ± {np.std(fps_values):.1f}')
    print('')
    
    return results


def main():
    print('=' * 70)
    print('DATABASE PERFORMANCE COMPARISON')
    print('=' * 70)
    print('')
    
    # Load config to check database availability
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Check which databases are available
    legacy_available = False
    multiple_available = False
    
    try:
        with open(config['database']['path'], 'rb') as f:
            face_db = pickle.load(f)
        if len(face_db) > 0:
            legacy_available = True
            print('Legacy database: AVAILABLE')
    except:
        print('Legacy database: NOT AVAILABLE')
    
    try:
        db = EmbeddingDatabase(config['database']['embeddings_dir'])
        db.load()
        if db.get_total_embedding_count() > 0:
            multiple_available = True
            print('Multiple embedding database: AVAILABLE')
    except:
        print('Multiple embedding database: NOT AVAILABLE')
    
    print('')
    
    if not legacy_available and not multiple_available:
        print('ERROR: No databases available for testing')
        print('Please populate at least one database before running comparison')
        return
    
    # Run tests
    results = []
    
    if legacy_available:
        result = run_comparison_test('legacy', num_frames=100)
        if result:
            results.append(result)
    
    if multiple_available:
        result = run_comparison_test('multiple', num_frames=100)
        if result:
            results.append(result)
    
    # Comparison summary
    if len(results) >= 2:
        print('=' * 70)
        print('COMPARISON SUMMARY')
        print('=' * 70)
        print('')
        
        legacy = results[0]
        multiple = results[1]
        
        print(f'{"Metric":<30} | {"Legacy":<15} | {"Multiple":<15} | {"Difference":<15}')
        print('-' * 85)
        print(f'{"Avg Latency (ms)":<30} | {legacy["avg_latency_ms"]:<15.2f} | {multiple["avg_latency_ms"]:<15.2f} | {multiple["avg_latency_ms"] - legacy["avg_latency_ms"]:+.2f}')
        print(f'{"Avg Comparisons":<30} | {legacy["avg_comparisons"]:<15.1f} | {multiple["avg_comparisons"]:<15.1f} | {multiple["avg_comparisons"] - legacy["avg_comparisons"]:+.1f}')
        print(f'{"Average FPS":<30} | {legacy["avg_fps"]:<15.1f} | {multiple["avg_fps"]:<15.1f} | {multiple["avg_fps"] - legacy["avg_fps"]:+.1f}')
        print(f'{"FPS Stability (std)":<30} | {legacy["fps_std"]:<15.1f} | {multiple["fps_std"]:<15.1f} | {multiple["fps_std"] - legacy["fps_std"]:+.1f}')
        print('')
        
        # Analysis
        print('ANALYSIS:')
        
        latency_diff = multiple['avg_latency_ms'] - legacy['avg_latency_ms']
        if abs(latency_diff) < 1.0:
            print('  - Latency: Comparable (difference < 1ms)')
        elif latency_diff > 0:
            print(f'  - Latency: Multiple mode is {latency_diff:.1f}ms slower')
        else:
            print(f'  - Latency: Multiple mode is {abs(latency_diff):.1f}ms faster')
        
        comp_diff = multiple['avg_comparisons'] - legacy['avg_comparisons']
        print(f'  - Comparisons: Multiple mode performs {comp_diff:.0f} more comparisons per recognition')
        
        fps_diff = multiple['avg_fps'] - legacy['avg_fps']
        if abs(fps_diff) < 2.0:
            print('  - FPS: Comparable (difference < 2 FPS)')
        elif fps_diff > 0:
            print(f'  - FPS: Multiple mode is {fps_diff:.1f} FPS faster')
        else:
            print(f'  - FPS: Multiple mode is {abs(fps_diff):.1f} FPS slower')
        
        print('')
        print('=' * 70)
        print('CONCLUSION:')
        print('=' * 70)
        
        # Overall assessment
        if abs(latency_diff) < 2.0 and abs(fps_diff) < 3.0:
            print('  Both modes have comparable performance.')
            print('  Multiple embedding mode can be safely adopted.')
        elif latency_diff > 5.0 or fps_diff < -5.0:
            print('  Multiple embedding mode has noticeable performance impact.')
            print('  Consider optimization before full deployment.')
        else:
            print('  Multiple embedding mode has acceptable performance overhead.')
            print('  Trade-off between accuracy and speed is reasonable.')
        
        print('')
    else:
        print('Not enough data for comparison (need both databases populated)')


if __name__ == '__main__':
    main()