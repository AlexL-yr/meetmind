"""ChromaDB indexer for meeting ground-truth documents."""
import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

GROUND_TRUTH_DIR = Path("audit_cases/ground_truth")
_COLLECTION_NAME = "ground_truth"


class GroundTruthIndexer:
    """Indexes ground-truth JSON files into ChromaDB using local embeddings."""

    def __init__(self, persist_dir: str = "./chroma_db") -> None:
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def index_document(self, transcript_id: str, ground_truth: dict) -> None:
        """Embed and upsert a single ground-truth document."""
        text = json.dumps(ground_truth, ensure_ascii=False)
        embedding = self.model.encode(text).tolist()
        self.collection.upsert(
            ids=[transcript_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "transcript_id": transcript_id,
                "defect_type": ground_truth.get("defect_type", ""),
            }],
        )

    def index_all(self, ground_truth_dir: Path = GROUND_TRUTH_DIR) -> int:
        """Index all *.json files in ground_truth_dir. Returns count indexed."""
        if not ground_truth_dir.exists():
            return 0
        count = 0
        for filepath in sorted(ground_truth_dir.glob("*.json")):
            with open(filepath, encoding="utf-8") as f:
                ground_truth = json.load(f)
            self.index_document(filepath.stem, ground_truth)
            count += 1
        return count

    def get_collection(self) -> chromadb.Collection:
        return self.collection

    def count(self) -> int:
        return self.collection.count()
