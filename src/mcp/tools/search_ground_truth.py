"""Semantic similarity search over the ChromaDB ground-truth collection."""


def search_ground_truth(query: str, n_results: int = 3) -> list[dict]:
    """Return the *n* most semantically similar ground-truth documents for *query*.

    Useful when the exact transcript_id is unknown — embed the query text and
    retrieve the closest cases by cosine similarity.

    Args:
        query: Free-text query (e.g. a transcript excerpt or keyword description).
        n_results: Number of results to return (default 3).

    Returns:
        List of ground-truth dicts ordered by similarity, or a single error dict.
    """
    try:
        from ...rag.singleton import get_retriever
        retriever = get_retriever()
        if retriever is None:
            return [{"error": "ChromaDB index is empty. Run: python run_audit.py --index"}]
        return retriever.search_similar(query, n_results=n_results)
    except Exception as exc:
        return [{"error": str(exc)}]
