import cv2
import numpy as np
from typing import Tuple, Dict, Any, Optional, List
from src.recognition.recognizer import Models


class FrameValidator:
    """
    Frame validation layer for video and image enrollment.
    
    Validates whether a frame is suitable for enrollment before
    passing it to the Enrollment Engine.
    
    Validation checks (progressive):
        1. Exactly one face detected
        2. Minimum face size
        3. Detection confidence threshold
        4. Blur detection (Variance of Laplacian)
    
    The validator does NOT extract embeddings or save to database.
    It only validates frame suitability and returns validated face data.
    
    Architecture:
        - validate(frame): Convenience wrapper with internal detection
        - validate_with_faces(faces, frame): Optimized path with pre-detected faces
    """
    
    def __init__(self, 
                 min_face_size: int = 80,
                 min_face_confidence: float = 0.7,
                 max_blur_score: float = 100.0):
        """
        Initialize frame validator.
        
        Args:
            min_face_size: Minimum face width/height in pixels
            min_face_confidence: Minimum detection confidence (0.0 - 1.0)
            max_blur_score: Maximum blur score (Variance of Laplacian)
                           Lower = sharper, Higher = more blurry
        """
        self.min_face_size = min_face_size
        self.min_face_confidence = min_face_confidence
        self.max_blur_score = max_blur_score
        self.models = Models()
    
    def validate(self, frame: np.ndarray) -> Tuple[bool, str]:
        """
        Validate a frame for enrollment (convenience wrapper).
        
        Performs face detection internally. For better performance,
        use validate_with_faces() with pre-detected faces.
        
        Args:
            frame: BGR frame (numpy array)
        
        Returns:
            (is_valid, reason)
                is_valid: True if frame is suitable for enrollment
                reason: Description of validation result
        """
        faces = self.models.detect_and_recognize(frame)
        return self.validate_with_faces(faces, frame)
    
    def validate_with_faces(self, 
                           faces: List[Any], 
                           frame: np.ndarray) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate frame with pre-detected faces.
        
        This method avoids duplicate face detection. The face detection
        should be performed once externally, then passed to this method.
        
        Args:
            faces: List of detected faces from InsightFace
            frame: BGR frame (numpy array)
        
        Returns:
            (is_valid, face_data)
                is_valid: True if frame is suitable for enrollment
                face_data: Dict with validated face information (if valid)
                          None if validation failed
        """
        # Validation Rule 1: Exactly one face
        if len(faces) == 0:
            return False, None
        
        if len(faces) > 1:
            return False, None
        
        face = faces[0]
        
        # Extract face information
        bbox = face.bbox.astype(int)
        confidence = getattr(face, 'det_score', 0.0)  # Detection confidence
        embedding = face.embedding
        face_size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])  # Width or height
        
        # Validation Rule 2: Minimum face size
        if face_size < self.min_face_size:
            return False, None
        
        # Validation Rule 3: Detection confidence
        if confidence < self.min_face_confidence:
            return False, None
        
        # Validation Rule 4: Blur detection
        blur_score = self._compute_blur_score(frame, bbox)
        if blur_score > self.max_blur_score:
            return False, None
        
        # All validations passed - return face data
        face_data = {
            'face': face,
            'embedding': embedding,
            'bbox': bbox,
            'confidence': confidence,
            'face_size': face_size,
            'blur_score': blur_score
        }
        
        return True, face_data
    
    def _compute_blur_score(self, frame: np.ndarray, bbox: np.ndarray) -> float:
        """
        Compute blur score using Variance of Laplacian.
        
        Computed on cropped face region, not entire frame.
        Lower score = sharper image
        Higher score = more blurry
        
        Args:
            frame: Full frame (BGR)
            bbox: Face bounding box [x1, y1, x2, y2]
        
        Returns:
            Blur score (variance of Laplacian)
        """
        # Crop face region
        x1, y1, x2, y2 = bbox
        face_crop = frame[y1:y2, x1:x2]
        
        if face_crop.size == 0:
            return float('inf')  # Invalid crop
        
        # Convert to grayscale
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        
        # Compute Laplacian variance
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        return blur_score
    
    def has_face(self, frame: np.ndarray) -> bool:
        """
        Quick check if frame contains at least one face.
        
        Args:
            frame: BGR frame
        
        Returns:
            True if face detected, False otherwise
        """
        faces = self.models.detect_and_recognize(frame)
        return len(faces) > 0
    
    def get_face_count(self, frame: np.ndarray) -> int:
        """
        Count number of faces in frame.
        
        Args:
            frame: BGR frame
        
        Returns:
            Number of faces detected
        """
        faces = self.models.detect_and_recognize(frame)
        return len(faces)