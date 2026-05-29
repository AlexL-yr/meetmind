"""Shared RAG retriever singleton — loaded once per process."""
from __future__ import annotations

_retriever = None
_init_attempted = False


def get_retriever(chroma_dir: str = "./chroma_db"):
    """Return the shared GroundTruthRetriever, or None if ChromaDB is empty/unavailable."""
    global _retriever, _init_attempted
    if _init_attempted:
        return _retriever
    _init_attempted = True
    try:
        from .indexer import GroundTruthIndexer
        from .retriever import GroundTruthRetriever
        indexer = GroundTruthIndexer(persist_dir=chroma_dir)
        if indexer.count() > 0:
            _retriever = GroundTruthRetriever(indexer)
    except Exception:
        pass
    return _retriever
