from app.pruner import prune_context


def test_context_pruning_reduction():
    raw_chunks = ["Duplicate content text"] * 5
    assert len(prune_context(raw_chunks, max_similarity=0.8)) < len(raw_chunks)


def test_empty_context_is_safe():
    assert prune_context([], max_tokens=10) == []