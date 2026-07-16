import cv2
import numpy as np
import os
import csv
from datetime import datetime
from typing import Tuple, Dict, Any, List
from src.recognition.recognizer import Models
from src.database.database import EmbeddingDatabase


class EnrollmentEngine:
    """
    Common enrollment engine for image and video enrollment.
    
    Pipeline:
        Image/Frame → Face Detection → Embedding Extraction → 
        L2 Normalization → Duplicate Check → Save
    
    Both image and video enrollment use the same embedding generation process.
    """
    
    def __init__(self, duplicate_threshold: float = 0.995, models=None):
        self.duplicate_threshold = duplicate_threshold
        self.models = models if models is not None else Models()
        self.enrollment_log: List[Dict[str, Any]] = []
    
    def enroll_image(self, 
                     image: np.ndarray, 
                     image_path: str,
                     person_name: str, 
                     database: EmbeddingDatabase) -> Tuple[bool, str, float]:
        """
        Enroll a single image (with internal face detection).
        
        Convenience method that performs face detection internally.
        
        Args:
            image: BGR image (numpy array)
            image_path: Path or filename for logging
            person_name: Name of the person
            database: Embedding database instance
        
        Returns:
            (success, message, similarity_score)
        """
        return self._process_face(image, image_path, person_name, database, source_type="image")
    
    def enroll_with_face(self,
                        face_data: Dict[str, Any],
                        source_identifier: str,
                        person_name: str,
                        database: EmbeddingDatabase,
                        source_type: str = "image") -> Tuple[bool, str, float]:
        """
        Enroll using pre-validated face data.
        
        This method avoids duplicate face detection. Use this when
        face detection has already been performed by FrameValidator.
        
        Args:
            face_data: Validated face data from FrameValidator
                      Contains: embedding, bbox, confidence, blur_score
            source_identifier: Image path or frame ID for logging
            person_name: Name of the person
            database: Embedding database instance
            source_type: "image" or "video" for logging
        
        Returns:
            (success, message, similarity_score)
        """
        return self._process_validated_face(face_data, source_identifier, person_name, 
                                           database, source_type)
    
    def _process_validated_face(self,
                                face_data: Dict[str, Any],
                                source_identifier: str,
                                person_name: str,
                                database: EmbeddingDatabase,
                                source_type: str = "image") -> Tuple[bool, str, float]:
        source_label = "IMAGE" if source_type == "image" else "VIDEO"

        embedding = face_data['embedding']
        confidence = face_data['confidence']
        
        # L2 Normalize embedding
        embedding_norm = embedding / np.linalg.norm(embedding)
        
        # Duplicate Check
        is_duplicate, similarity = self._check_duplicate(
            embedding_norm, 
            person_name, 
            database
        )
        
        if is_duplicate:
            msg = f"Duplicate embedding (similarity={similarity:.4f} > threshold={self.duplicate_threshold})"
            result = (False, msg, similarity)
            self._log_result(source_identifier, "DUPLICATE", "Duplicate embedding", similarity, 
                           source_label, "", confidence, 0)
            return result
        
        # Save embedding
        emb_path = database.add_embedding(person_name, embedding_norm)
        emb_filename = os.path.basename(emb_path) if emb_path else ""
        
        msg = "Enrollment successful"
        result = (True, msg, 1.0)
        self._log_result(source_identifier, "SUCCESS", "Enrolled", 1.0, source_label, 
                        emb_filename, confidence, 0)
        return result
    
    def _process_face(self, 
                      image: np.ndarray,
                      source_identifier: str,
                      person_name: str, 
                      database: EmbeddingDatabase,
                      source_type: str = "image") -> Tuple[bool, str, float]:
        source_label = "IMAGE" if source_type == "image" else "VIDEO"

        faces = self.models.detect_and_recognize(image)
        if len(faces) == 0:
            result = (False, "No face detected", 0.0)
            self._log_result(source_identifier, "FAILED", "No face detected", 0.0, source_label, "")
            return result
        
        if len(faces) > 1:
            msg = f"Multiple faces detected ({len(faces)}). Only one face allowed per enrollment."
            result = (False, msg, 0.0)
            self._log_result(source_identifier, "FAILED", "Multiple faces", 0.0, source_label, "")
            return result
        
        face = faces[0]
        
        embedding = face.embedding
        embedding_norm = embedding / np.linalg.norm(embedding)

        is_duplicate, similarity = self._check_duplicate(
            embedding_norm, 
            person_name, 
            database
        )
        
        if is_duplicate:
            msg = f"Duplicate embedding (similarity={similarity:.4f} > threshold={self.duplicate_threshold})"
            result = (False, msg, similarity)
            self._log_result(source_identifier, "DUPLICATE", "Duplicate embedding", similarity, source_label, "")
            return result

        emb_path = database.add_embedding(person_name, embedding_norm)
        emb_filename = os.path.basename(emb_path) if emb_path else ""

        msg = "Enrollment successful"
        result = (True, msg, 1.0)
        self._log_result(source_identifier, "SUCCESS", "Enrolled", 1.0, source_label, emb_filename)
        return result
    
    def _log_result(self, filename: str, status: str, reason: str, similarity: float,
                     source: str = "IMAGE", embedding_filename: str = "",
                     face_confidence: float = 0.0, frame_index: int = 0):
        self.enrollment_log.append({
            'filename': filename,
            'frame_index': frame_index,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'source': source,
            'face_confidence': f"{face_confidence:.4f}",
            'embedding_filename': embedding_filename,
            'status': status,
            'reason': reason,
            'similarity': f"{similarity:.4f}"
        })
    
    def clear_log(self):
        """Clear enrollment log for new session."""
        self.enrollment_log = []
    
    def _check_duplicate(self, 
                        new_embedding: np.ndarray, 
                        person_name: str, 
                        database: EmbeddingDatabase) -> Tuple[bool, float]:
        """
        Check if new embedding is duplicate of existing embeddings.
        
        Compares new embedding against all existing embeddings of the same person.
        If cosine similarity > threshold, consider it duplicate.
        
        Args:
            new_embedding: Normalized embedding to check
            person_name: Name of the person
            database: Embedding database instance
        
        Returns:
            (is_duplicate, max_similarity)
        """
        existing_embeddings = database.get_all_embeddings().get(person_name, [])
        
        if len(existing_embeddings) == 0:
            return False, 0.0
        
        max_similarity = 0.0
        
        for existing_emb in existing_embeddings:
            # Both already normalized
            similarity = np.dot(new_embedding, existing_emb)
            if similarity > max_similarity:
                max_similarity = similarity
        
        is_duplicate = max_similarity > self.duplicate_threshold
        
        return is_duplicate, max_similarity