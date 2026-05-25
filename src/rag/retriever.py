"""Semantic retrieval of ground-truth documents from ChromaDB."""
import json
from typing import Optional

from .indexer import GroundTruthIndexer


class GroundTruthRetriever:
    """Retrieves ground-truth documents by ID or semantic similarity."""

    def __init__(self, indexer: GroundTruthIndexer) -> None:
        self.indexer = indexer
        self.collection = indexer.get_collection()

    def get_by_id(self, transcript_id: str) -> Optional[dict]:
        """Direct lookup by transcript_id. Returns None if not found."""
        try:
            result = self.collection.get(ids=[transcript_id])
            if result["documents"]:
                return json.loads(result["documents"][0])
        except Exception:
            pass
        return None

    def search_similar(self, query: str, n_results: int = 3) -> list[dict]:
        """Return the n most semantically similar ground-truth documents."""
        embedding = self.indexer.model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=min(n_results, self.indexer.count() or 1),
        )
        return [json.loads(doc) for doc in results["documents"][0]]
