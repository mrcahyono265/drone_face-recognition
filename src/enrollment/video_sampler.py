import cv2
import numpy as np
from typing import Generator, Tuple


class VideoFrameSampler:
    """
    Time-based frame sampler for video enrollment.
    
    Extracts frames from video at configurable time intervals.
    This ensures consistent sampling regardless of video FPS.
    
    Example:
        sampling_interval_ms = 300  # Sample every 300ms
        For 30 FPS video: ~every 9 frames
        For 25 FPS video: ~every 7.5 frames
    """
    
    def __init__(self, sampling_interval_ms: int = 300):
        """
        Initialize video frame sampler.
        
        Args:
            sampling_interval_ms: Time interval between frames in milliseconds
        """
        self.sampling_interval_ms = sampling_interval_ms
    
    def sample(self, video_path: str) -> Generator[Tuple[np.ndarray, int, float], None, None]:
        """
        Sample frames from video at time-based intervals.
        
        Args:
            video_path: Path to video file
        
        Yields:
            (frame, frame_index, timestamp_ms)
                frame: BGR frame (numpy array)
                frame_index: Original frame number in video
                timestamp_ms: Timestamp in milliseconds
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise IOError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0  # Default fallback
        
        # Calculate frame interval based on FPS
        frame_interval = int(fps * self.sampling_interval_ms / 1000.0)
        frame_interval = max(1, frame_interval)  # At least every frame
        
        frame_index = 0
        sampled_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample at intervals
            if frame_index % frame_interval == 0:
                timestamp_ms = (frame_index / fps) * 1000.0
                yield frame, frame_index, timestamp_ms
                sampled_count += 1
            
            frame_index += 1
        
        cap.release()
    
    def get_video_info(self, video_path: str) -> dict:
        """
        Get video metadata.
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dictionary with video information
        """
        cap = cv2.VideoCapture(video_path)
        
        info = {
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration_seconds': 0.0
        }
        
        if info['fps'] > 0:
            info['duration_seconds'] = info['total_frames'] / info['fps']
        
        cap.release()
        return info