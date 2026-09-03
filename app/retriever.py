import re
import os
from dataclasses import asdict
from .ingestion import Chunk


def _terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class HybridRetriever:
    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self._encoder = None
        self._dense_enabled = os.getenv("PRUNERAG_ENABLE_DENSE", "false").lower() == "true"

    def _get_encoder(self):
        if self._dense_enabled and self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self._dense_enabled = False
        return self._encoder

    def add(self, chunks: list[Chunk]) -> None:
        self.chunks.extend(chunks)

    def search(self, query: str, limit: int = 8) -> list[dict]:
        query_terms = _terms(query)
        dense_scores = []
        encoder = self._get_encoder()
        if encoder and self.chunks:
            embeddings = encoder.encode([query] + [chunk.text for chunk in self.chunks], normalize_embeddings=True)
            dense_scores = [float(embeddings[0] @ embedding) for embedding in embeddings[1:]]
        scored = []
        for index, chunk in enumerate(self.chunks):
            chunk_terms = _terms(chunk.text)
            lexical = len(query_terms & chunk_terms) / max(1, len(query_terms))
            dense = dense_scores[index] if dense_scores else 0.0
            hybrid = (0.55 * dense) + (0.45 * lexical) if dense_scores else lexical
            scored.append((hybrid, index, chunk))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [{**asdict(chunk), "score": round(score, 4)} for score, _, chunk in scored[:limit] if score > 0]