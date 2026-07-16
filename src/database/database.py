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
    
    def load(self):
        self.embeddings = {}

        if not os.path.exists(self.db_root):
            print(f"[WARNING] Database directory not found: {self.db_root}")
            return

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

    def add_embedding(self, person_name, embedding):
        person_dir = os.path.join(self.db_root, person_name)
        os.makedirs(person_dir, exist_ok=True)

        existing = glob(os.path.join(person_dir, "emb_*.npy"))
        next_id = len(existing) + 1

        emb_path = os.path.join(person_dir, f"emb_{next_id:04d}.npy")
        np.save(emb_path, embedding)
        if person_name not in self.embeddings:
            self.embeddings[person_name] = []
        self.embeddings[person_name].append(embedding)

        print(f"[INFO] Added embedding for {person_name}: {emb_path}")
        return emb_path

    def get_all_embeddings(self):
        return self.embeddings

    def get_person_names(self):
        return list(self.embeddings.keys())

    def get_embedding_count(self, person_name):
        return len(self.embeddings.get(person_name, []))

    def get_total_embedding_count(self):
        return sum(len(embs) for embs in self.embeddings.values())


if __name__ == "__main__":
    import tempfile, shutil
    tmpdir = tempfile.mkdtemp()
    db = EmbeddingDatabase(tmpdir)

    rng = np.random.default_rng(42)
    emb1 = rng.standard_normal(512).astype(np.float32)
    emb1 /= np.linalg.norm(emb1)
    emb2 = rng.standard_normal(512).astype(np.float32)
    emb2 /= np.linalg.norm(emb2)

    db.add_embedding("alice", emb1)
    db.add_embedding("alice", emb2)
    db.add_embedding("bob", emb1)

    db2 = EmbeddingDatabase(tmpdir)
    db2.load()

    assert db2.get_total_embedding_count() == 3
    assert set(db2.get_person_names()) == {"alice", "bob"}
    assert db2.get_embedding_count("alice") == 2
    assert db2.get_embedding_count("bob") == 1

    all_embs = db2.get_all_embeddings()
    assert len(all_embs["alice"]) == 2
    assert len(all_embs["bob"]) == 1
    for name, embs in all_embs.items():
        for e in embs:
            assert abs(np.linalg.norm(e) - 1.0) < 1e-6

    shutil.rmtree(tmpdir)
    print("[OK] database.py self-check passed")