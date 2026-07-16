import cv2
import numpy as np
from typing import Tuple, Dict, Any, Optional, List
from src.recognition.recognizer import Models


class FrameValidator:
    def __init__(self, min_face_size=80, min_face_confidence=0.7, max_blur_score=100.0, models=None):
        self.min_face_size = min_face_size
        self.min_face_confidence = min_face_confidence
        self.max_blur_score = max_blur_score
        self.models = models if models is not None else Models()

    def validate_with_faces(self, faces, frame):
        if len(faces) == 0:
            return False, None
        if len(faces) > 1:
            return False, None

        face = faces[0]
        bbox = face.bbox.astype(int)
        confidence = getattr(face, 'det_score', 0.0)
        embedding = face.embedding
        face_size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])

        if face_size < self.min_face_size:
            return False, None
        if confidence < self.min_face_confidence:
            return False, None

        blur_score = self.compute_blur_score(frame, bbox)
        if blur_score > self.max_blur_score:
            return False, None

        return True, {
            'face': face, 'embedding': embedding, 'bbox': bbox,
            'confidence': confidence, 'face_size': face_size, 'blur_score': blur_score
        }

    def compute_blur_score(self, frame, bbox):
        x1, y1, x2, y2 = bbox
        face_crop = frame[y1:y2, x1:x2]
        if face_crop.size == 0:
            return float('inf')
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    val = FrameValidator(min_face_size=80, max_blur_score=650)

    uniform = np.ones((200, 200, 3), dtype=np.uint8) * 128
    score = val.compute_blur_score(uniform, (10, 10, 100, 100))
    assert score < 10, f"uniform image should have low blur, got {score}"

    sharp = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
    score = val.compute_blur_score(sharp, (10, 10, 100, 100))
    assert score > 10, f"noisy image should have high blur, got {score}"

    score = val.compute_blur_score(uniform, (10, 10, 10, 10))
    assert score == float('inf'), f"zero-size crop should give inf, got {score}"

    print("[OK] frame_validator.py self-check passed")