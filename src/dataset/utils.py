"""
Dataset utilities for automated enrollment pipeline.

Provides functions for scanning dataset structure, discovering identities,
and locating enrollment files based on configuration.
"""

import os
from typing import List


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


def get_enrollment_images_path(dataset_root, identity, enrollment_images_subdir):
    return os.path.join(dataset_root, identity, enrollment_images_subdir)


def get_enrollment_videos_path(dataset_root, identity, enrollment_videos_subdir):
    return os.path.join(dataset_root, identity, enrollment_videos_subdir)


def scan_files(directory, supported_formats):
    if not os.path.exists(directory):
        return []
    files = []
    for f in os.listdir(directory):
        if os.path.splitext(f)[1].lower() in supported_formats:
            files.append(os.path.join(directory, f))
    return sorted(files)