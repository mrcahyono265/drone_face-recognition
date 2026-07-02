import os
import cv2
import yaml
import time
import numpy as np
from collections import defaultdict
from src.database.database import EmbeddingDatabase
from src.enrollment.engine import EnrollmentEngine
from src.enrollment.frame_validator import FrameValidator
from src.enrollment.video_sampler import VideoFrameSampler
import shutil


def run_sensitivity_analysis():
    """
    Threshold sensitivity analysis.
    
    Evaluates multiple threshold combinations to select optimal values
    based on experimental evidence.
    """
    
    # Load base config
    with open('config.yaml', 'r') as f:
        base_config = yaml.safe_load(f)
    
    # Threshold combinations to test
    duplicate_thresholds = [0.995, 0.990, 0.985, 0.980]
    blur_thresholds = [500, 650, 700]
    
    print('=' * 70)
    print('THRESHOLD SENSITIVITY ANALYSIS')
    print('=' * 70)
    print('')
    print(f'Duplicate thresholds: {duplicate_thresholds}')
    print(f'Blur thresholds: {blur_thresholds}')
    print(f'Total configurations: {len(duplicate_thresholds) * len(blur_thresholds)}')
    print('')
    
    # Results storage
    results = []
    
    # Clean database before each run
    db_path = base_config['database']['embeddings_dir']
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    os.makedirs(db_path)
    
    # Test each configuration
    for dup_thresh in duplicate_thresholds:
        for blur_thresh in blur_thresholds:
            config_key = f'dup={dup_thresh:.3f}, blur={blur_thresh}'
            print(f'Testing: {config_key}')
            print('-' * 70)
            
            # Re-initialize for each configuration
            database = EmbeddingDatabase(db_path)
            database.load()
            
            enroller = EnrollmentEngine(duplicate_threshold=dup_thresh)
            enroller.clear_log()
            
            validator = FrameValidator(
                min_face_size=base_config['enrollment']['validation']['min_face_size'],
                min_face_confidence=base_config['enrollment']['validation']['min_face_confidence'],
                max_blur_score=blur_thresh
            )
            
            # Statistics
            stats = {
                'duplicate_threshold': dup_thresh,
                'blur_threshold': blur_thresh,
                'total_processed': 0,
                'accepted': 0,
                'rejected_total': 0,
                'rejected_blur': 0,
                'rejected_confidence': 0,
                'rejected_size': 0,
                'rejected_no_face': 0,
                'duplicates': 0,
                'stored_embeddings': 0,
                'processing_time': 0.0
            }
            
            start_time = time.time()
            
            # Process dataset
            dataset_dir = 'dataset'
            for person_name in sorted(os.listdir(dataset_dir)):
                person_dir = os.path.join(dataset_dir, person_name)
                if not os.path.isdir(person_dir):
                    continue
                
                # Images
                images_dir = os.path.join(person_dir, 'enrollment', 'images')
                if os.path.exists(images_dir):
                    for img_file in sorted(os.listdir(images_dir)):
                        if not img_file.endswith(('.jpg', '.jpeg', '.png')):
                            continue
                        
                        img_path = os.path.join(images_dir, img_file)
                        image = cv2.imread(img_path)
                        
                        if image is None:
                            continue
                        
                        stats['total_processed'] += 1
                        
                        # Detect and validate
                        faces = enroller.models.detect_and_recognize(image)
                        is_valid, face_data = validator.validate_with_faces(faces, image)
                        
                        if is_valid:
                            success, msg, sim = enroller.enroll_with_face(
                                face_data, img_file, person_name, database, source_type='image'
                            )
                            if success:
                                stats['accepted'] += 1
                            elif 'Duplicate' in msg:
                                stats['duplicates'] += 1
                        else:
                            stats['rejected_total'] += 1
                            # Determine rejection reason
                            if len(faces) == 0:
                                stats['rejected_no_face'] += 1
                            else:
                                face = faces[0]
                                bbox = face.bbox.astype(int)
                                face_size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
                                confidence = getattr(face, 'det_score', 0.0)
                                blur_score = validator._compute_blur_score(image, bbox)
                                
                                if face_size < validator.min_face_size:
                                    stats['rejected_size'] += 1
                                elif confidence < validator.min_face_confidence:
                                    stats['rejected_confidence'] += 1
                                elif blur_score > validator.max_blur_score:
                                    stats['rejected_blur'] += 1
            
                # Videos (sample 3 frames per video for speed)
                videos_dir = os.path.join(person_dir, 'enrollment', 'videos')
                if os.path.exists(videos_dir):
                    sampler = VideoFrameSampler(sampling_interval_ms=2000)  # Every 2s for speed
                    
                    for vid_file in sorted(os.listdir(videos_dir)):
                        if not vid_file.endswith(('.mp4', '.avi', '.mov')):
                            continue
                        
                        vid_path = os.path.join(videos_dir, vid_file)
                        frame_count = 0
                        
                        for frame, frame_idx, timestamp_ms in sampler.sample(vid_path):
                            if frame_count >= 3:  # Limit for speed
                                break
                            
                            stats['total_processed'] += 1
                            
                            faces = enroller.models.detect_and_recognize(frame)
                            is_valid, face_data = validator.validate_with_faces(faces, frame)
                            
                            if is_valid:
                                frame_id = f'frame_{frame_idx:06d}'
                                success, msg, sim = enroller.enroll_with_face(
                                    face_data, frame_id, person_name, database, source_type='video'
                                )
                                if success:
                                    stats['accepted'] += 1
                                elif 'Duplicate' in msg:
                                    stats['duplicates'] += 1
                            else:
                                stats['rejected_total'] += 1
                                if len(faces) == 0:
                                    stats['rejected_no_face'] += 1
                            
                            frame_count += 1
            
            stats['processing_time'] = time.time() - start_time
            stats['stored_embeddings'] = database.get_total_embedding_count()
            
            # Store results
            results.append(stats)
            
            print(f'  Processed: {stats["total_processed"]}')
            print(f'  Accepted: {stats["accepted"]} ({stats["accepted"]/stats["total_processed"]*100:.1f}%)')
            print(f'  Rejected: {stats["rejected_total"]} ({stats["rejected_total"]/stats["total_processed"]*100:.1f}%)')
            print(f'  Duplicates: {stats["duplicates"]}')
            print(f'  Stored: {stats["stored_embeddings"]}')
            print(f'  Time: {stats["processing_time"]:.2f}s')
            print('')
            
            # Clean database for next run
            if os.path.exists(db_path):
                shutil.rmtree(db_path)
            os.makedirs(db_path)
    
    # Print comparison table
    print('=' * 70)
    print('COMPARISON TABLE')
    print('=' * 70)
    print('')
    
    # Header
    print(f'{"Dup Thresh":>12} | {"Blur Thresh":>11} | {"Processed":>9} | {"Accepted":>8} | {"Rejected":>8} | {"Duplicates":>10} | {"Stored":>6} | {"Time (s)":>8}')
    print('-' * 95)
    
    for r in results:
        print(f'{r["duplicate_threshold"]:>12.3f} | {r["blur_threshold"]:>11.0f} | {r["total_processed"]:>9} | {r["accepted"]:>8} | {r["rejected_total"]:>8} | {r["duplicates"]:>10} | {r["stored_embeddings"]:>6} | {r["processing_time"]:>8.2f}')
    
    print('')
    
    # Analysis by duplicate threshold
    print('=' * 70)
    print('ANALYSIS BY DUPLICATE THRESHOLD')
    print('=' * 70)
    print('')
    
    for dup_thresh in duplicate_thresholds:
        matching = [r for r in results if r['duplicate_threshold'] == dup_thresh]
        avg_stored = np.mean([r['stored_embeddings'] for r in matching])
        avg_duplicates = np.mean([r['duplicates'] for r in matching])
        avg_pass_rate = np.mean([r['accepted']/r['total_processed']*100 for r in matching])
        
        print(f'Duplicate Threshold: {dup_thresh:.3f}')
        print(f'  Avg Stored Embeddings: {avg_stored:.0f}')
        print(f'  Avg Duplicates Detected: {avg_duplicates:.1f}')
        print(f'  Avg Pass Rate: {avg_pass_rate:.1f}%')
        print('')
    
    # Analysis by blur threshold
    print('=' * 70)
    print('ANALYSIS BY BLUR THRESHOLD')
    print('=' * 70)
    print('')
    
    for blur_thresh in blur_thresholds:
        matching = [r for r in results if r['blur_threshold'] == blur_thresh]
        avg_rejected_blur = np.mean([r['rejected_blur'] for r in matching])
        avg_pass_rate = np.mean([r['accepted']/r['total_processed']*100 for r in matching])
        
        print(f'Blur Threshold: {blur_thresh}')
        print(f'  Avg Rejected by Blur: {avg_rejected_blur:.1f}')
        print(f'  Avg Pass Rate: {avg_pass_rate:.1f}%')
        print('')
    
    # Rejection breakdown for best configuration
    print('=' * 70)
    print('RECOMMENDED CONFIGURATION')
    print('=' * 70)
    print('')
    
    # Find configuration with best balance
    # Criteria: High pass rate, reasonable duplicates, not too many stored
    best_config = None
    best_score = 0
    
    for r in results:
        pass_rate = r['accepted'] / r['total_processed'] * 100
        # Score: high pass rate + some duplicate filtering + reasonable storage
        score = pass_rate + (r['duplicates'] * 0.5) - (r['stored_embeddings'] * 0.01)
        
        if score > best_score:
            best_score = score
            best_config = r
    
    if best_config:
        print(f'Recommended: duplicate_threshold={best_config["duplicate_threshold"]:.3f}, blur_threshold={best_config["blur_threshold"]}')
        print('')
        print(f'  Total Processed: {best_config["total_processed"]}')
        print(f'  Accepted: {best_config["accepted"]} ({best_config["accepted"]/best_config["total_processed"]*100:.1f}%)')
        print(f'  Rejected: {best_config["rejected_total"]} ({best_config["rejected_total"]/best_config["total_processed"]*100:.1f}%)')
        print(f'  Duplicates: {best_config["duplicates"]}')
        print(f'  Stored Embeddings: {best_config["stored_embeddings"]}')
        print(f'  Processing Time: {best_config["processing_time"]:.2f}s')
        print('')
        print('  Rejection Breakdown:')
        print(f'    No Face: {best_config["rejected_no_face"]}')
        print(f'    Blur: {best_config["rejected_blur"]}')
        print(f'    Confidence: {best_config["rejected_confidence"]}')
        print(f'    Size: {best_config["rejected_size"]}')
    
    print('')
    print('=' * 70)
    print('SENSITIVITY ANALYSIS COMPLETE')
    print('=' * 70)


if __name__ == '__main__':
    run_sensitivity_analysis()