"""
Dataset utilities for automated enrollment pipeline.

Provides functions for scanning dataset structure, discovering identities,
and locating enrollment files based on configuration.
"""

import os
from typing import List, Dict
from pathlib import Path


def get_all_identities(dataset_root: str) -> List[str]:
    """
    Scan dataset root directory and return list of identity names.
    
    Identities are determined by subdirectory names in the dataset root.
    Only directories are considered (files are ignored).
    
    Args:
        dataset_root: Path to dataset root directory
        
    Returns:
        List of identity names (directory names), sorted alphabetically
    """
    if not os.path.exists(dataset_root):
        print(f"[WARNING] Dataset root not found: {dataset_root}")
        return []
    
    identities = []
    for item in os.listdir(dataset_root):
        item_path = os.path.join(dataset_root, item)
        if os.path.isdir(item_path):
            identities.append(item)
    
    return sorted(identities)


def get_enrollment_images_path(dataset_root: str, identity: str, enrollment_images_subdir: str) -> str:
    """
    Get path to enrollment images directory for a specific identity.
    
    Args:
        dataset_root: Path to dataset root directory
        identity: Identity name (subdirectory name)
        enrollment_images_subdir: Subdirectory path for enrollment images (from config)
        
    Returns:
        Full path to enrollment images directory
    """
    return os.path.join(dataset_root, identity, enrollment_images_subdir)


def get_enrollment_videos_path(dataset_root: str, identity: str, enrollment_videos_subdir: str) -> str:
    """
    Get path to enrollment videos directory for a specific identity.
    
    Args:
        dataset_root: Path to dataset root directory
        identity: Identity name (subdirectory name)
        enrollment_videos_subdir: Subdirectory path for enrollment videos (from config)
        
    Returns:
        Full path to enrollment videos directory
    """
    return os.path.join(dataset_root, identity, enrollment_videos_subdir)


def scan_images(directory: str, supported_formats: List[str]) -> List[str]:
    """
    Scan directory for image files with supported formats.
    
    Only scans the immediate directory (non-recursive).
    File matching is case-insensitive.
    
    Args:
        directory: Path to directory to scan
        supported_formats: List of supported file extensions (e.g., ['.jpg', '.jpeg'])
        
    Returns:
        List of full paths to image files, sorted alphabetically
    """
    if not os.path.exists(directory):
        return []
    
    image_files = []
    for filename in os.listdir(directory):
        ext = os.path.splitext(filename)[1].lower()
        if ext in supported_formats:
            image_files.append(os.path.join(directory, filename))
    
    return sorted(image_files)


def scan_videos(directory: str, supported_formats: List[str]) -> List[str]:
    """
    Scan directory for video files with supported formats.
    
    Only scans the immediate directory (non-recursive).
    File matching is case-insensitive.
    
    Args:
        directory: Path to directory to scan
        supported_formats: List of supported file extensions (e.g., ['.mp4'])
        
    Returns:
        List of full paths to video files, sorted alphabetically
    """
    if not os.path.exists(directory):
        return []
    
    video_files = []
    for filename in os.listdir(directory):
        ext = os.path.splitext(filename)[1].lower()
        if ext in supported_formats:
            video_files.append(os.path.join(directory, filename))
    
    return sorted(video_files)


def ensure_directory_exists(directory: str) -> bool:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        directory: Path to directory
        
    Returns:
        True if directory exists or was created, False if creation failed
    """
    if os.path.exists(directory):
        return True
    
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create directory {directory}: {e}")
        return False


def get_database_embedding_path(embeddings_dir: str, identity: str) -> str:
    """
    Get path to embedding directory for a specific identity.
    
    Args:
        embeddings_dir: Root embeddings directory (from config)
        identity: Identity name
        
    Returns:
        Full path to identity's embedding directory
    """
    return os.path.join(embeddings_dir, identity)


def count_existing_embeddings(embeddings_dir: str, identity: str) -> int:
    """
    Count number of existing embeddings for an identity.
    
    Args:
        embeddings_dir: Root embeddings directory
        identity: Identity name
        
    Returns:
        Number of .npy files in identity's embedding directory
    """
    emb_dir = get_database_embedding_path(embeddings_dir, identity)
    if not os.path.exists(emb_dir):
        return 0
    
    count = 0
    for filename in os.listdir(emb_dir):
        if filename.endswith('.npy') and filename.startswith('emb_'):
            count += 1
    
    return count