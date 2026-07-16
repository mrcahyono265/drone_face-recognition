"""
Automated Video Enrollment Tool

Scans all identities in dataset directory and enrolls frames from videos automatically.
No manual input required - fully automated based on dataset structure.

Dataset structure:
    dataset/
        <identity>/
            enrollment/
                videos/
                    *.mp4

Pipeline:
    Video → Sample Frames → Validate (blur, face, confidence) → 
    Enroll Valid Frames → Save Embeddings

Output:
    database/embeddings/<identity>/emb_0001.npy, etc.
    reports/enrollment/video_report.csv
"""

import cv2
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.database import EmbeddingDatabase
from src.enrollment.engine import EnrollmentEngine
from src.enrollment.video_sampler import VideoFrameSampler
from src.enrollment.frame_validator import FrameValidator
from src.recognition.recognizer import Models
from src.dataset.utils import (
    get_all_identities,
    get_enrollment_videos_path,
    scan_videos,
    ensure_directory_exists
)
from src.utils import load_config, initialize_csv_report, append_to_csv_report, validate_embeddings


VIDEO_REPORT_HEADERS = [
    'timestamp',
    'identity',
    'video_file',
    'frame_index',
    'status',
    'similarity',
    'embedding_file',
    'face_confidence',
    'blur_score',
    'reason'
]


def process_video(
    enroller: EnrollmentEngine,
    database: EmbeddingDatabase,
    validator: FrameValidator,
    sampler: VideoFrameSampler,
    identity: str,
    video_path: str,
    report_path: str,
    verbose: bool
) -> Dict[str, Any]:
    """
    Process all frames from a single video.
    
    Returns:
        Dictionary with enrollment statistics
    """
    stats = {
        'total_frames': 0,
        'valid_frames': 0,
        'success': 0,
        'duplicate': 0,
        'no_face': 0,
        'low_confidence': 0,
        'blurry': 0,
        'multiple_faces': 0,
        'failed': 0,
        'saved_files': []
    }
    
    video_filename = os.path.basename(video_path)
    
    if verbose:
        print(f"  Video: {video_filename}")
    
    # Get video info
    video_info = sampler.get_video_info(video_path)
    duration = video_info['duration_seconds']
    total_video_frames = video_info['total_frames']
    
    if verbose:
        print(f"    Duration: {duration:.2f}s, Total Frames: {total_video_frames}")
        print("")
    
    try:
        # Sample frames from video
        for frame, frame_index, timestamp_ms in sampler.sample(video_path):
            stats['total_frames'] += 1
            
            if verbose and stats['total_frames'] % 10 == 0:
                print(f"    Processing frame {stats['total_frames']}...")
            
            # Validate frame (blur, face detection, confidence)
            # First detect faces
            faces = validator.models.detect_and_recognize(frame)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check validation rules progressively to determine exact failure reason
            reason = None
            
            # Rule 1: No face
            if len(faces) == 0:
                reason = "no_face"
                stats['no_face'] += 1
                append_to_csv_report(report_path, [
                    timestamp, identity, video_filename, frame_index,
                    'no_face', '', '', '', '', reason
                ])
                continue
            
            # Rule 2: Multiple faces
            if len(faces) > 1:
                reason = "multiple_faces"
                stats['multiple_faces'] += 1
                append_to_csv_report(report_path, [
                    timestamp, identity, video_filename, frame_index,
                    'multiple_faces', '', '', '', '', reason
                ])
                continue
            
            # Now validate the single face
            is_valid, face_data = validator.validate_with_faces(faces, frame)
            
            if not is_valid:
                # Determine reason from face_data or re-check conditions
                face = faces[0]
                bbox = face.bbox.astype(int)
                confidence = getattr(face, 'det_score', 0.0)
                face_size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
                
                # Check confidence
                if confidence < validator.min_face_confidence:
                    reason = "low_confidence"
                    stats['low_confidence'] += 1
                    append_to_csv_report(report_path, [
                        timestamp, identity, video_filename, frame_index,
                        'low_confidence', '', '', f"{confidence:.4f}", '', reason
                    ])
                else:
                    # Check blur (need to compute)
                    blur_score = validator.compute_blur_score(frame, bbox)
                    if blur_score > validator.max_blur_score:
                        reason = "blurry"
                        stats['blurry'] += 1
                        append_to_csv_report(report_path, [
                            timestamp, identity, video_filename, frame_index,
                            'blurry', '', '', '', f"{blur_score:.2f}", reason
                        ])
                    else:
                        reason = "failed"
                        stats['failed'] += 1
                        append_to_csv_report(report_path, [
                            timestamp, identity, video_filename, frame_index,
                            'failed', '', '', '', '', reason
                        ])
                
                continue
            
            # Frame is valid, enroll it
            stats['valid_frames'] += 1
            
            success, message, similarity = enroller.enroll_with_face(
                face_data,
                f"{video_filename}_frame{frame_index}",
                identity,
                database,
                source_type="video"
            )
            
            if success:
                stats['success'] += 1
                
                # Get saved embedding filename
                person_dir = os.path.join(database.db_root, identity)
                emb_files = sorted([f for f in os.listdir(person_dir) if f.endswith('.npy')])
                if emb_files:
                    saved_file = emb_files[-1]
                    stats['saved_files'].append(saved_file)
                    append_to_csv_report(report_path, [
                        timestamp, identity, video_filename, frame_index,
                        'success', f'{similarity:.4f}', saved_file,
                        f"{face_data['confidence']:.4f}", f"{face_data['blur_score']:.2f}",
                        message
                    ])
            else:
                if "Duplicate" in message:
                    stats['duplicate'] += 1
                    append_to_csv_report(report_path, [
                        timestamp, identity, video_filename, frame_index,
                        'duplicate', f'{similarity:.4f}', '',
                        f"{face_data['confidence']:.4f}", f"{face_data['blur_score']:.2f}",
                        message
                    ])
                else:
                    stats['failed'] += 1
                    append_to_csv_report(report_path, [
                        timestamp, identity, video_filename, frame_index,
                        'failed', f'{similarity:.4f}', '',
                        f"{face_data['confidence']:.4f}", f"{face_data['blur_score']:.2f}",
                        message
                    ])
            
            if verbose and stats['success'] % 5 == 0:
                print(f"    Enrolled: {stats['success']} frames")
    
    except Exception as e:
        print(f"    [ERROR] Failed to process video: {e}")
        stats['failed'] += 1
    
    if verbose:
        print("")
        print(f"  Video Summary:")
        print(f"    Total Frames Sampled: {stats['total_frames']}")
        print(f"    Valid Frames: {stats['valid_frames']}")
        print(f"    Successfully Enrolled: {stats['success']}")
        print(f"    Duplicates Skipped: {stats['duplicate']}")
        print(f"    No Face: {stats['no_face']}")
        print(f"    Low Confidence: {stats['low_confidence']}")
        print(f"    Blurry: {stats['blurry']}")
        print(f"    Multiple Faces: {stats['multiple_faces']}")
        print(f"    Failed: {stats['failed']}")
        print("")
    
    return stats


def print_identity_summary(identity: str, stats: Dict[str, Any], database: EmbeddingDatabase) -> None:
    """Print enrollment summary for a single identity"""
    print(f"  Identity Summary: {identity}")
    print(f"    Total Videos: {stats.get('video_count', 1)}")
    print(f"    Total Frames Sampled: {stats['total_frames']}")
    print(f"    Valid Frames: {stats['valid_frames']}")
    print(f"    Successfully Enrolled: {stats['success']}")
    print(f"    Duplicates Skipped: {stats['duplicate']}")
    print(f"    No Face: {stats['no_face']}")
    print(f"    Low Confidence: {stats['low_confidence']}")
    print(f"    Blurry: {stats['blurry']}")
    print(f"    Multiple Faces: {stats['multiple_faces']}")
    print(f"    Failed: {stats['failed']}")
    print(f"    Embeddings Stored: {database.get_embedding_count(identity)}")
    print("")


def main():
    print("=== Automated Video Enrollment Pipeline ===")
    print("")
    
    # Load configuration
    config = load_config()
    
    # Extract configuration values
    dataset_root = config["dataset"]["root"]
    enrollment_videos_subdir = config["dataset"]["enrollment_videos"]
    supported_formats = config["dataset"].get("supported_video_formats", [".mp4"])
    embeddings_dir = config["database"]["embeddings_dir"]
    duplicate_threshold = config["enrollment"]["duplicate_threshold"]
    sampling_interval_ms = config["enrollment"]["sampling_interval_ms"]
    verbose = config["logging"].get("verbose", False)
    
    # Validation parameters
    validation_config = config["enrollment"].get("validation", {})
    min_face_size = validation_config.get("min_face_size", 80)
    min_face_confidence = validation_config.get("min_face_confidence", 0.7)
    max_blur_score = validation_config.get("max_blur_score", 650)
    
    # Ensure database directory exists
    if not ensure_directory_exists(embeddings_dir):
        print("[ERROR] Failed to create database directory")
        return
    
    # Get all identities
    identities = get_all_identities(dataset_root)
    
    if len(identities) == 0:
        print(f"[ERROR] No identities found in dataset: {dataset_root}")
        print("[INFO] Please create dataset structure:")
        print(f"  {dataset_root}/")
        print(f"    <identity>/")
        print(f"      enrollment/")
        print(f"        videos/")
        return
    
    print(f"Dataset Root: {dataset_root}")
    print(f"Identities Found: {', '.join(identities)}")
    print("")
    
    # Initialize database
    database = EmbeddingDatabase(embeddings_dir)
    database.load()
    
    # Initialize face recognition model (shared)
    models = Models()
    
    # Initialize enrollment engine
    enroller = EnrollmentEngine(duplicate_threshold=duplicate_threshold, models=models)
    
    # Initialize video sampler
    sampler = VideoFrameSampler(sampling_interval_ms=sampling_interval_ms)
    
    # Initialize frame validator (shared model)
    validator = FrameValidator(
        min_face_size=min_face_size,
        min_face_confidence=min_face_confidence,
        max_blur_score=max_blur_score,
        models=models
    )
    
    # Initialize CSV report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(
        config["reports"]["enrollment_dir"],
        f"video_report_{timestamp}.csv"
    )
    initialize_csv_report(report_path, VIDEO_REPORT_HEADERS)
    
    # Store overall statistics
    overall_stats = {
        'total_frames': 0,
        'valid_frames': 0,
        'success': 0,
        'duplicate': 0,
        'no_face': 0,
        'low_confidence': 0,
        'blurry': 0,
        'multiple_faces': 0,
        'failed': 0,
        'identities_processed': 0,
        'videos_processed': 0
    }
    
    # Process each identity
    for identity in identities:
        print(f"Processing Identity: {identity}")
        
        # Get videos directory
        videos_dir = get_enrollment_videos_path(dataset_root, identity, enrollment_videos_subdir)
        
        # Scan for videos
        video_files = scan_videos(videos_dir, supported_formats)
        
        if len(video_files) == 0:
            print(f"  [SKIP] No videos found in {videos_dir}")
            print("")
            continue
        
        print(f"  Found {len(video_files)} video(s)")
        print("")
        
        # Accumulate stats for this identity
        identity_stats = {
            'total_frames': 0,
            'valid_frames': 0,
            'success': 0,
            'duplicate': 0,
            'no_face': 0,
            'low_confidence': 0,
            'blurry': 0,
            'multiple_faces': 0,
            'failed': 0,
            'saved_files': [],
            'video_count': len(video_files)
        }
        
        # Process each video
        for video_path in video_files:
            video_stats = process_video(
                enroller, database, validator, sampler,
                identity, video_path, report_path, verbose
            )
            
            # Accumulate stats
            for key in identity_stats:
                if key in video_stats and key != 'saved_files':
                    identity_stats[key] += video_stats[key]
                elif key == 'saved_files':
                    identity_stats[key].extend(video_stats['saved_files'])
            
            overall_stats['videos_processed'] += 1
        
        # Print identity summary
        print_identity_summary(identity, identity_stats, database)
        
        # Accumulate overall stats
        for key in overall_stats:
            if key == 'identities_processed':
                overall_stats[key] += 1
            elif key in identity_stats and key != 'saved_files':
                overall_stats[key] += identity_stats[key]
    
    # Print overall summary
    print("=" * 70)
    print("=== Overall Summary ===")
    print(f"Total Identities: {overall_stats['identities_processed']}")
    print(f"Total Videos Processed: {overall_stats['videos_processed']}")
    print(f"Total Frames Sampled: {overall_stats['total_frames']}")
    print(f"Total Valid Frames: {overall_stats['valid_frames']}")
    print(f"Total Success: {overall_stats['success']}")
    print(f"Total Duplicate: {overall_stats['duplicate']}")
    print(f"Total No Face: {overall_stats['no_face']}")
    print(f"Total Low Confidence: {overall_stats['low_confidence']}")
    print(f"Total Blurry: {overall_stats['blurry']}")
    print(f"Total Multiple Faces: {overall_stats['multiple_faces']}")
    print(f"Total Failed: {overall_stats['failed']}")
    
    # Print database statistics
    print("")
    print("=== Database Statistics ===")
    total_embeddings = 0
    for identity in identities:
        count = database.get_embedding_count(identity)
        total_embeddings += count
        print(f"  {identity}: {count} embedding(s)")
    
    print(f"Total Embeddings Stored: {total_embeddings}")
    print("")
    
    # Validate embeddings
    validate_embeddings(database, identities)
    print("")
    
    # Print report location
    print(f"CSV Report: {report_path}")
    print("")
    print("=== Enrollment Complete ===")


if __name__ == "__main__":
    main()