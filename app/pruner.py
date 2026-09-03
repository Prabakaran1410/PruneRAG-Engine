import re
from collections.abc import Iterable


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _similarity(left: str, right: str) -> float:
    a, b = _tokens(left), _tokens(right)
    return len(a & b) / max(1, len(a | b))


def prune_context(chunks: Iterable[str], max_similarity: float = 0.88, max_tokens: int = 2000, min_score: float | None = None) -> list[str]:
    selected: list[str] = []
    for chunk in chunks:
        if not chunk.strip() or any(_similarity(chunk, kept) > max_similarity for kept in selected):
            continue
        selected.append(chunk)
    if min_score is not None:
        selected = [chunk for chunk in selected if min_score <= 0.0 or len(_tokens(chunk)) >= 1]
    result: list[str] = []
    used = 0
    for chunk in selected:
        words = chunk.split()
        if used + len(words) > max_tokens:
            remaining = max_tokens - used
            if remaining > 0:
                result.append(" ".join(words[:remaining]))
            break
        result.append(chunk)
        used += len(words)
    return result