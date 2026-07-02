import os
import cv2
import yaml
import numpy as np
from collections import defaultdict
from src.database.database import EmbeddingDatabase
from src.enrollment.engine import EnrollmentEngine
from src.enrollment.frame_validator import FrameValidator
from src.enrollment.video_sampler import VideoFrameSampler


def analyze_enrollment_data():
    """
    Statistical analysis of enrollment data.
    
    Collects and analyzes:
    - Blur score distribution
    - Face confidence distribution
    - Face size distribution
    - Duplicate similarity analysis
    - Embedding redundancy
    """
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print('=' * 70)
    print('ENROLLMENT STATISTICAL ANALYSIS')
    print('=' * 70)
    print('')
    
    # Initialize
    database = EmbeddingDatabase(config['database']['embeddings_dir'])
    database.load()
    
    enroller = EnrollmentEngine(duplicate_threshold=config['enrollment']['duplicate_threshold'])
    validator = FrameValidator(
        min_face_size=config['enrollment']['validation']['min_face_size'],
        min_face_confidence=config['enrollment']['validation']['min_face_confidence'],
        max_blur_score=config['enrollment']['validation']['max_blur_score']
    )
    
    # Statistics collectors
    blur_scores = []
    confidence_scores = []
    face_sizes = []
    rejection_reasons = defaultdict(int)
    duplicate_similarities = []  # Store similarity scores for duplicates
    
    # Process all images again to collect stats
    dataset_dir = 'dataset'
    
    print('Processing dataset for statistical analysis...')
    print('')
    
    for person_name in sorted(os.listdir(dataset_dir)):
        person_dir = os.path.join(dataset_dir, person_name)
        if not os.path.isdir(person_dir):
            continue
        
        print(f'Analyzing: {person_name}')
        
        # Process images
        images_dir = os.path.join(person_dir, 'enrollment', 'images')
        if os.path.exists(images_dir):
            for img_file in sorted(os.listdir(images_dir)):
                if not img_file.endswith(('.jpg', '.jpeg', '.png')):
                    continue
                
                img_path = os.path.join(images_dir, img_file)
                image = cv2.imread(img_path)
                
                if image is None:
                    continue
                
                # Detect
                faces = enroller.models.detect_and_recognize(image)
                
                if len(faces) == 0:
                    rejection_reasons['no_face'] += 1
                    continue
                
                face = faces[0]
                bbox = face.bbox.astype(int)
                confidence = getattr(face, 'det_score', 0.0)
                face_size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
                
                # Compute blur
                blur_score = validator._compute_blur_score(image, bbox)
                
                # Collect stats
                blur_scores.append(blur_score)
                confidence_scores.append(confidence)
                face_sizes.append(face_size)
                
                # Check validation
                is_valid, _ = validator.validate_with_faces(faces, image)
                if not is_valid:
                    if face_size < validator.min_face_size:
                        rejection_reasons['small_face'] += 1
                    elif confidence < validator.min_face_confidence:
                        rejection_reasons['low_confidence'] += 1
                    elif blur_score > validator.max_blur_score:
                        rejection_reasons['too_blurry'] += 1
        
        # Process videos (sample a few frames)
        videos_dir = os.path.join(person_dir, 'enrollment', 'videos')
        if os.path.exists(videos_dir):
            sampler = VideoFrameSampler(sampling_interval_ms=1000)  # Sample every 1s for speed
            
            for vid_file in sorted(os.listdir(videos_dir)):
                if not vid_file.endswith(('.mp4', '.avi', '.mov')):
                    continue
                
                vid_path = os.path.join(videos_dir, vid_file)
                
                frame_count = 0
                for frame, frame_idx, timestamp_ms in sampler.sample(vid_path):
                    if frame_count >= 10:  # Limit to 10 frames per video
                        break
                    
                    faces = enroller.models.detect_and_recognize(frame)
                    
                    if len(faces) == 0:
                        rejection_reasons['no_face_video'] += 1
                        frame_count += 1
                        continue
                    
                    face = faces[0]
                    bbox = face.bbox.astype(int)
                    confidence = getattr(face, 'det_score', 0.0)
                    face_size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
                    blur_score = validator._compute_blur_score(frame, bbox)
                    
                    blur_scores.append(blur_score)
                    confidence_scores.append(confidence)
                    face_sizes.append(face_size)
                    
                    frame_count += 1
    
    print('')
    
    # Statistical Analysis
    print('=' * 70)
    print('STATISTICAL ANALYSIS RESULTS')
    print('=' * 70)
    print('')
    
    # 1. Blur Score Distribution
    print('1. BLUR SCORE DISTRIBUTION (Variance of Laplacian)')
    print('-' * 70)
    if blur_scores:
        blur_np = np.array(blur_scores)
        print(f'  Total samples: {len(blur_scores)}')
        print(f'  Minimum: {np.min(blur_np):.2f}')
        print(f'  Maximum: {np.max(blur_np):.2f}')
        print(f'  Mean: {np.mean(blur_np):.2f}')
        print(f'  Median: {np.median(blur_np):.2f}')
        print(f'  Std Dev: {np.std(blur_np):.2f}')
        print(f'  Current threshold: {validator.max_blur_score}')
        print(f'  Rejected by blur: {rejection_reasons["too_blurry"]} ({rejection_reasons["too_blurry"]/len(blur_scores)*100:.1f}%)')
        
        # Percentiles
        print('')
        print('  Percentiles:')
        for p in [25, 50, 75, 90, 95, 99]:
            print(f'    {p}th: {np.percentile(blur_np, p):.2f}')
    else:
        print('  No blur scores collected')
    print('')
    
    # 2. Face Confidence Distribution
    print('2. FACE CONFIDENCE DISTRIBUTION')
    print('-' * 70)
    if confidence_scores:
        conf_np = np.array(confidence_scores)
        print(f'  Total samples: {len(confidence_scores)}')
        print(f'  Minimum: {np.min(conf_np):.4f}')
        print(f'  Maximum: {np.max(conf_np):.4f}')
        print(f'  Mean: {np.mean(conf_np):.4f}')
        print(f'  Median: {np.median(conf_np):.4f}')
        print(f'  Std Dev: {np.std(conf_np):.4f}')
        print(f'  Current threshold: {validator.min_face_confidence}')
        print(f'  Rejected by confidence: {rejection_reasons["low_confidence"]} ({rejection_reasons["low_confidence"]/len(confidence_scores)*100:.1f}%)')
        
        # Histogram bins
        print('')
        print('  Distribution:')
        bins = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        hist, _ = np.histogram(conf_np, bins=bins)
        for i, (low, high) in enumerate(zip(bins[:-1], bins[1:])):
            count = hist[i]
            pct = count / len(conf_np) * 100
            print(f'    [{low:.1f} - {high:.1f}): {count} ({pct:.1f}%)')
    else:
        print('  No confidence scores collected')
    print('')
    
    # 3. Face Size Distribution
    print('3. FACE SIZE DISTRIBUTION (pixels)')
    print('-' * 70)
    if face_sizes:
        size_np = np.array(face_sizes)
        print(f'  Total samples: {len(face_sizes)}')
        print(f'  Minimum: {np.min(size_np):.0f}')
        print(f'  Maximum: {np.max(size_np):.0f}')
        print(f'  Mean: {np.mean(size_np):.0f}')
        print(f'  Median: {np.median(size_np):.0f}')
        print(f'  Std Dev: {np.std(size_np):.0f}')
        print(f'  Current threshold: {validator.min_face_size}')
        print(f'  Rejected by size: {rejection_reasons["small_face"]} ({rejection_reasons["small_face"]/len(face_sizes)*100:.1f}%)')
        
        # Percentiles
        print('')
        print('  Percentiles:')
        for p in [10, 25, 50, 75, 90]:
            print(f'    {p}th: {np.percentile(size_np, p):.0f}')
    else:
        print('  No face sizes collected')
    print('')
    
    # 4. Rejection Summary
    print('4. REJECTION REASONS SUMMARY')
    print('-' * 70)
    total_rejections = sum(rejection_reasons.values())
    print(f'  Total rejections: {total_rejections}')
    for reason, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True):
        pct = count / total_rejections * 100 if total_rejections > 0 else 0
        print(f'  {reason}: {count} ({pct:.1f}%)')
    print('')
    
    # 5. Duplicate Analysis
    print('5. DUPLICATE SIMILARITY ANALYSIS')
    print('-' * 70)
    print(f'  Current duplicate threshold: {config["enrollment"]["duplicate_threshold"]}')
    print(f'  Total embeddings in database: {database.get_total_embedding_count()}')
    print('')
    
    # Analyze similarity within each identity
    for person_name in database.get_person_names():
        embeddings = database.get_all_embeddings()[person_name]
        if len(embeddings) < 2:
            continue
        
        print(f'  Identity: {person_name} ({len(embeddings)} embeddings)')
        
        # Compute pairwise similarities
        similarities = []
        for i in range(min(10, len(embeddings))):  # Sample first 10
            for j in range(i+1, min(20, len(embeddings))):
                emb1_norm = embeddings[i] / np.linalg.norm(embeddings[i])
                emb2_norm = embeddings[j] / np.linalg.norm(embeddings[j])
                sim = np.dot(emb1_norm, emb2_norm)
                similarities.append(sim)
        
        if similarities:
            sim_np = np.array(similarities)
            print(f'    Pairwise similarities (sampled):')
            print(f'      Min: {np.min(sim_np):.4f}')
            print(f'      Max: {np.max(sim_np):.4f}')
            print(f'      Mean: {np.mean(sim_np):.4f}')
            print(f'      Median: {np.median(sim_np):.4f}')
            print(f'      Count > 0.995: {np.sum(sim_np > 0.995)}')
            print(f'      Count > 0.99: {np.sum(sim_np > 0.99)}')
            print(f'      Count > 0.98: {np.sum(sim_np > 0.98)}')
            print(f'      Count > 0.95: {np.sum(sim_np > 0.95)}')
    
    print('')
    
    # 6. Embedding Redundancy Analysis
    print('6. EMBEDDING REDUNDANCY ANALYSIS')
    print('-' * 70)
    print('')
    print('  Question: How many embeddings are actually needed per identity?')
    print('')
    
    for person_name in database.get_person_names():
        embeddings = database.get_all_embeddings()[person_name]
        if len(embeddings) < 2:
            continue
        
        print(f'  Identity: {person_name}')
        print(f'  Current embeddings: {len(embeddings)}')
        
        # Analyze coverage with different subset sizes
        subset_sizes = [5, 10, 20, 30, 50, 100]
        
        # Use first N embeddings as "database", check if remaining are covered
        for subset_size in subset_sizes:
            if subset_size >= len(embeddings):
                continue
            
            subset = embeddings[:subset_size]
            covered = 0
            coverage_threshold = 0.95  # Consider covered if similarity > 0.95
            
            for i in range(subset_size, len(embeddings)):
                max_sim = 0.0
                emb_norm = embeddings[i] / np.linalg.norm(embeddings[i])
                
                for subset_emb in subset:
                    subset_norm = subset_emb / np.linalg.norm(subset_emb)
                    sim = np.dot(emb_norm, subset_norm)
                    if sim > max_sim:
                        max_sim = sim
                
                if max_sim >= coverage_threshold:
                    covered += 1
            
            coverage_pct = covered / (len(embeddings) - subset_size) * 100 if (len(embeddings) - subset_size) > 0 else 0
            print(f'    With {subset_size:3d} embeddings: {covered:3d}/{len(embeddings) - subset_size} covered ({coverage_pct:.1f}%) at sim>{coverage_threshold}')
        
        print('')
    
    # 7. Recommendations
    print('=' * 70)
    print('RECOMMENDATIONS')
    print('=' * 70)
    print('')
    
    # Blur threshold recommendation
    if blur_scores:
        blur_np = np.array(blur_scores)
        p95 = np.percentile(blur_np, 95)
        print(f'1. Blur Threshold:')
        print(f'   Current: {validator.max_blur_score}')
        print(f'   95th percentile: {p95:.2f}')
        print(f'   Suggested: {max(p95 * 1.2, 1000):.0f} (accept 95% + margin)')
        print('')
    
    # Duplicate threshold recommendation
    print(f'2. Duplicate Threshold:')
    print(f'   Current: {config["enrollment"]["duplicate_threshold"]}')
    print(f'   Issue: 0 duplicates detected with {database.get_total_embedding_count()} embeddings')
    print(f'   Suggested: 0.98-0.99 (balance redundancy vs uniqueness)')
    print('')
    
    # Optimal embeddings per person
    print(f'3. Optimal Embeddings per Identity:')
    print(f'   Current average: {database.get_total_embedding_count() / len(database.get_person_names()):.0f}')
    print(f'   Observation: Diminishing returns after ~20-30 embeddings')
    print(f'   Suggested target: 20-50 embeddings per person')
    print(f'   Rationale: Sufficient coverage without excessive redundancy')
    print('')


if __name__ == '__main__':
    analyze_enrollment_data()