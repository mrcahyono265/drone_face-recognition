"""
Dataset utilities module.
"""

from .utils import (
    get_all_identities,
    get_enrollment_images_path,
    get_enrollment_videos_path,
    scan_images,
    scan_videos,
    ensure_directory_exists,
    get_database_embedding_path,
    count_existing_embeddings
)

__all__ = [
    'get_all_identities',
    'get_enrollment_images_path',
    'get_enrollment_videos_path',
    'scan_images',
    'scan_videos',
    'ensure_directory_exists',
    'get_database_embedding_path',
    'count_existing_embeddings'
]