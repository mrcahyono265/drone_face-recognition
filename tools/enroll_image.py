"""
Automated Image Enrollment Tool

Scans all identities in dataset directory and enrolls images automatically.
No manual input required - fully automated based on dataset structure.

Dataset structure:
    dataset/
        <identity>/
            enrollment/
                images/
                    *.jpg, *.jpeg

Output:
    database/embeddings/<identity>/emb_0001.npy, etc.
    reports/enrollment/image_report.csv
"""

import cv2
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.database import EmbeddingDatabase
from src.enrollment.engine import EnrollmentEngine
from src.dataset.utils import (
    get_all_identities,
    get_enrollment_images_path,
    scan_images,
    ensure_directory_exists
)
from src.utils import load_config, initialize_csv_report, append_to_csv_report, validate_embeddings


IMAGE_REPORT_HEADERS = [
    'timestamp',
    'identity',
    'source_file',
    'status',
    'similarity',
    'embedding_file'
]


def process_identity(
    enroller: EnrollmentEngine,
    database: EmbeddingDatabase,
    identity: str,
    images_dir: str,
    image_files: List[str],
    report_path: str,
    verbose: bool
) -> Dict[str, Any]:
    """
    Process all images for a single identity.
    
    Returns:
        Dictionary with enrollment statistics
    """
    stats = {
        'total': len(image_files),
        'success': 0,
        'duplicate': 0,
        'no_face': 0,
        'multiple_faces': 0,
        'failed': 0,
        'saved_files': []
    }
    
    if verbose:
        print(f"  Scanning: {images_dir}")
        print(f"  Found {len(image_files)} image(s)")
        print("")
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        
        if verbose:
            print(f"  [{i}/{len(image_files)}] {filename}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            if verbose:
                print(f"    [FAILED] Cannot read image")
            stats['failed'] += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            append_to_csv_report(report_path, [
                timestamp, identity, filename, 'failed', '', ''
            ])
            continue
        
        # Enroll
        success, message, similarity = enroller.enroll_image(
            image, filename, identity, database
        )
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if success:
            if verbose:
                print(f"    [SUCCESS] {message}")
            stats['success'] += 1
            
            # Get saved embedding filename
            person_dir = os.path.join(database.db_root, identity)
            emb_files = sorted([f for f in os.listdir(person_dir) if f.endswith('.npy')])
            if emb_files:
                saved_file = emb_files[-1]
                stats['saved_files'].append(saved_file)
                append_to_csv_report(report_path, [
                    timestamp, identity, filename, 'success', f'{similarity:.4f}', saved_file
                ])
        else:
            if "Duplicate" in message:
                if verbose:
                    print(f"    [DUPLICATE] {message}")
                stats['duplicate'] += 1
                append_to_csv_report(report_path, [
                    timestamp, identity, filename, 'duplicate', f'{similarity:.4f}', ''
                ])
            elif "No face" in message:
                if verbose:
                    print(f"    [NO FACE] {message}")
                stats['no_face'] += 1
                append_to_csv_report(report_path, [
                    timestamp, identity, filename, 'no_face', '', ''
                ])
            elif "Multiple faces" in message:
                if verbose:
                    print(f"    [MULTIPLE] {message}")
                stats['multiple_faces'] += 1
                append_to_csv_report(report_path, [
                    timestamp, identity, filename, 'multiple_faces', '', ''
                ])
            else:
                if verbose:
                    print(f"    [FAILED] {message}")
                stats['failed'] += 1
                append_to_csv_report(report_path, [
                    timestamp, identity, filename, 'failed', '', ''
                ])
        
        if verbose:
            print("")
    
    return stats


def print_identity_summary(identity: str, stats: Dict[str, Any], database: EmbeddingDatabase) -> None:
    """Print enrollment summary for a single identity"""
    print(f"  Identity Summary: {identity}")
    print(f"    Total: {stats['total']}")
    print(f"    Success: {stats['success']}")
    print(f"    Duplicate: {stats['duplicate']}")
    print(f"    No Face: {stats['no_face']}")
    print(f"    Multiple Faces: {stats['multiple_faces']}")
    print(f"    Failed: {stats['failed']}")
    print(f"    Embeddings Stored: {database.get_embedding_count(identity)}")
    print("")


def main():
    print("=== Automated Image Enrollment Pipeline ===")
    print("")
    
    # Load configuration
    config = load_config()
    
    # Extract configuration values
    dataset_root = config["dataset"]["root"]
    enrollment_images_subdir = config["dataset"]["enrollment_images"]
    supported_formats = config["dataset"].get("supported_image_formats", [".jpg", ".jpeg"])
    embeddings_dir = config["database"]["embeddings_dir"]
    duplicate_threshold = config["enrollment"]["duplicate_threshold"]
    verbose = config["logging"].get("verbose", False)
    
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
        print(f"        images/")
        return
    
    print(f"Dataset Root: {dataset_root}")
    print(f"Identities Found: {', '.join(identities)}")
    print("")
    
    # Initialize database
    database = EmbeddingDatabase(embeddings_dir)
    database.load()
    
    # Initialize enrollment engine
    enroller = EnrollmentEngine(duplicate_threshold=duplicate_threshold)
    
    # Initialize CSV report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(
        config["reports"]["enrollment_dir"],
        f"image_report_{timestamp}.csv"
    )
    initialize_csv_report(report_path, IMAGE_REPORT_HEADERS)
    
    # Store overall statistics
    overall_stats = {
        'total': 0,
        'success': 0,
        'duplicate': 0,
        'no_face': 0,
        'multiple_faces': 0,
        'failed': 0,
        'identities_processed': 0
    }
    
    # Process each identity
    for identity in identities:
        print(f"Processing Identity: {identity}")
        
        # Get images directory
        images_dir = get_enrollment_images_path(dataset_root, identity, enrollment_images_subdir)
        
        # Scan for images
        image_files = scan_images(images_dir, supported_formats)
        
        if len(image_files) == 0:
            print(f"  [SKIP] No images found in {images_dir}")
            print("")
            continue
        
        # Process identity
        stats = process_identity(
            enroller, database, identity, images_dir, image_files, report_path, verbose
        )
        
        # Print identity summary
        print_identity_summary(identity, stats, database)
        
        # Accumulate overall stats
        for key in overall_stats:
            if key == 'identities_processed':
                overall_stats[key] += 1
            elif key in stats:
                overall_stats[key] += stats[key]
    
    # Print overall summary
    print("=" * 70)
    print("=== Overall Summary ===")
    print(f"Total Identities: {overall_stats['identities_processed']}")
    print(f"Total Images Processed: {overall_stats['total']}")
    print(f"Total Success: {overall_stats['success']}")
    print(f"Total Duplicate: {overall_stats['duplicate']}")
    print(f"Total No Face: {overall_stats['no_face']}")
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