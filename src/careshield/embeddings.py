from __future__ import annotations

import hashlib
import math

from careshield.retrieval import tokenize


class HashEmbeddingModel:
    """Small deterministic embedding model for offline tests and demos.

    This is not a semantic production embedding model. It deliberately mirrors
    the shape of a real embedding adapter while keeping the public demo free of
    API keys and network calls.
    """

    name = "local-hash-embedding-v1"

    def __init__(self, dimensions: int = 64) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimensions)]
        for token in tokenize(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
            bucket = int.from_bytes(digest[:2], "big") % self.dimensions
            vector[bucket] += 1.0
        return _l2_normalize(vector)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimensions")
    return sum(a * b for a, b in zip(left, right, strict=True))


def _l2_normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]
