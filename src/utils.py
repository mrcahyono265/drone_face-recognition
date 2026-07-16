import csv
import os
import sys
import yaml
from typing import Dict, List, Any

from src.database.database import EmbeddingDatabase


def _setup_cuda_paths():
    site_pkg = os.path.join(os.path.dirname(sys.executable), "..", "Lib", "site-packages")
    paths = [
        os.path.join(site_pkg, "nvidia", "cu13", "bin", "x86_64"),
        os.path.join(site_pkg, "nvidia", "cudnn", "bin"),
    ]
    for p in paths:
        p = os.path.abspath(p)
        if os.path.isdir(p) and p not in os.environ.get("PATH", ""):
            os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")


def load_config() -> Dict[str, Any]:
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print("[ERROR] config.yaml not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"[ERROR] Invalid YAML: {e}")
        sys.exit(1)


def initialize_csv_report(report_path: str, headers: List[str]) -> None:
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)


def append_to_csv_report(report_path: str, row: List) -> None:
    with open(report_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(row)


def validate_embeddings(database: EmbeddingDatabase, identities: List[str]) -> Dict[str, List[str]]:
    import numpy as np
    warnings = {
        'invalid_dimension': [],
        'not_normalized': []
    }
    print("Validating embeddings...")
    for identity in identities:
        emb_dir = os.path.join(database.db_root, identity)
        if not os.path.exists(emb_dir):
            continue
        for filename in os.listdir(emb_dir):
            if not filename.endswith('.npy'):
                continue
            emb_path = os.path.join(emb_dir, filename)
            try:
                embedding = np.load(emb_path)
                if embedding.shape != (512,):
                    warnings['invalid_dimension'].append(f"{identity}/{filename}: shape={embedding.shape}")
                norm = np.linalg.norm(embedding)
                if abs(norm - 1.0) > 1e-6:
                    warnings['not_normalized'].append(f"{identity}/{filename}: norm={norm:.6f}")
            except Exception as e:
                print(f"[WARNING] Failed to validate {emb_path}: {e}")
    if warnings['invalid_dimension']:
        print("\n[WARNING] Invalid dimension embeddings:")
        for w in warnings['invalid_dimension']:
            print(f"  - {w}")
    if warnings['not_normalized']:
        print("\n[WARNING] Embeddings not L2-normalized:")
        for w in warnings['not_normalized']:
            print(f"  - {w}")
    if not warnings['invalid_dimension'] and not warnings['not_normalized']:
        print("  All embeddings valid [OK]")
    return warnings
