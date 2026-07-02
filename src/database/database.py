import os
import numpy as np
from typing import Dict, List
from glob import glob


class EmbeddingDatabase:
    """
    Embedding database manager for Phase 2.
    
    Stores multiple embeddings per identity as individual .npy files.
    Loads all embeddings into memory at startup for fast real-time recognition.
    
    Directory structure:
        database/embeddings/
            ├── person_name/
            │   ├── emb_0001.npy
            │   ├── emb_0002.npy
            │   └── ...
            └── ...
    
    Each embedding is L2-normalized before saving to ensure consistency.
    Recognition compares query embedding against ALL stored embeddings
    and uses the highest cosine similarity as the identity score.
    """
    
    def __init__(self, db_root: str = "database/embeddings"):
        """
        Initialize embedding database.
        
        Args:
            db_root: Root directory for embedding storage
        """
        self.db_root = db_root
        self.embeddings: Dict[str, List[np.ndarray]] = {}
    
    def load(self) -> Dict[str, List[np.ndarray]]:
        """
        Load all embeddings from disk into memory.
        
        Scans the database directory structure and loads all .npy files
        for each person. Embeddings are stored in memory for fast access
        during real-time recognition.
        
        Returns:
            Dictionary mapping person_name -> list of embedding arrays
        """
        self.embeddings = {}
        
        if not os.path.exists(self.db_root):
            print(f"[WARNING] Database directory not found: {self.db_root}")
            return self.embeddings
        
        # Load each person's embeddings
        for person_name in os.listdir(self.db_root):
            person_dir = os.path.join(self.db_root, person_name)
            if not os.path.isdir(person_dir):
                continue
            
            person_embeddings = []
            for emb_path in sorted(glob(os.path.join(person_dir, "emb_*.npy"))):
                try:
                    embedding = np.load(emb_path)
                    person_embeddings.append(embedding)
                except Exception as e:
                    print(f"[WARNING] Failed to load {emb_path}: {e}")
            
            if person_embeddings:
                self.embeddings[person_name] = person_embeddings
                print(f"[INFO] Loaded {len(person_embeddings)} embeddings for {person_name}")
        
        total = sum(len(embs) for embs in self.embeddings.values())
        print(f"[INFO] Database loaded: {len(self.embeddings)} identities, {total} embeddings")
        
        return self.embeddings
    
    def add_embedding(self, person_name: str, embedding: np.ndarray) -> str:
        """
        Add a new embedding for a person.
        
        The embedding is L2-normalized before saving to ensure database
        consistency. File naming uses sequential numbering (emb_0001.npy,
        emb_0002.npy, etc.).
        
        Args:
            person_name: Name of the person
            embedding: Face embedding array (512-D)
        
        Returns:
            Path to saved embedding file
        """
        person_dir = os.path.join(self.db_root, person_name)
        os.makedirs(person_dir, exist_ok=True)
        
        # Get next sequence number
        existing = glob(os.path.join(person_dir, "emb_*.npy"))
        next_id = len(existing) + 1
        
        # L2 normalize embedding before saving
        embedding_norm = embedding / np.linalg.norm(embedding)
        
        # Save embedding
        emb_path = os.path.join(person_dir, f"emb_{next_id:04d}.npy")
        np.save(emb_path, embedding_norm)
        
        # Update in-memory cache
        if person_name not in self.embeddings:
            self.embeddings[person_name] = []
        self.embeddings[person_name].append(embedding_norm)
        
        print(f"[INFO] Added embedding for {person_name}: {emb_path}")
        return emb_path
    
    def get_all_embeddings(self) -> Dict[str, List[np.ndarray]]:
        """
        Get all loaded embeddings.
        
        Returns:
            Dictionary mapping person_name -> list of embedding arrays
        """
        return self.embeddings
    
    def get_person_names(self) -> List[str]:
        """
        Get list of all person names in database.
        
        Returns:
            List of person names
        """
        return list(self.embeddings.keys())
    
    def get_embedding_count(self, person_name: str) -> int:
        """
        Get number of embeddings for a specific person.
        
        Args:
            person_name: Name of the person
        
        Returns:
            Number of embeddings for that person
        """
        return len(self.embeddings.get(person_name, []))
    
    def get_total_embedding_count(self) -> int:
        """
        Get total number of embeddings in database.
        
        Returns:
            Total number of embeddings across all identities
        """
        return sum(len(embs) for embs in self.embeddings.values())