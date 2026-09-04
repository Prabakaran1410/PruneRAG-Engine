from app.pruner import prune_context
from app.ingestion import Chunk
from app.retriever import HybridRetriever


def test_context_pruning_reduction():
    raw_chunks = ["Duplicate content text"] * 5
    assert len(prune_context(raw_chunks, max_similarity=0.8)) < len(raw_chunks)


def test_empty_context_is_safe():
    assert prune_context([], max_tokens=10) == []


def test_fallback_retrieval_clears_relevance_threshold():
    retriever = HybridRetriever()
    retriever.add([Chunk("Q3 revenue was $48.2 million and adjusted EBITDA was $10.1 million.", "report.pdf", 1)])
    results = retriever.search("What was Q3 revenue and adjusted EBITDA?")
    assert results
    assert results[0]["score"] >= 0.65