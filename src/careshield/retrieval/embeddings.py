import hashlib
import math

import careshield.retrieval.keyword as keyword


class HashEmbeddingModel:
    """Deterministic embedding adapter for offline demos and tests."""

    name = "local-hash-embedding-v1"

    def __init__(self, *, dimensions: int = 64) -> None:
        """Create the local embedding adapter.

        :param dimensions: Number of vector dimensions to produce.
        """
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, *, text: str) -> list[float]:
        """Embed text into a normalized sparse hash vector.

        :param text: Text to embed.
        :return: Normalized vector representation.
        """
        vector = [0.0 for _ in range(self.dimensions)]

        # Hashing keeps the demo deterministic and dependency-light while still
        # preserving the vector-search shape used by production systems.
        for token in keyword.tokenize(text=text):
            digest = hashlib.blake2b(data=token.encode("utf-8"), digest_size=4).digest()
            bucket = int.from_bytes(bytes=digest[:2], byteorder="big") % self.dimensions
            vector[bucket] += 1.0

        return _l2_normalize(vector=vector)


def cosine_similarity(*, left: list[float], right: list[float]) -> float:
    """Calculate cosine similarity between normalized vectors.

    :param left: Left vector.
    :param right: Right vector.
    :return: Similarity score.
    """
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimensions")
    return sum(left_value * right_value for left_value, right_value in zip(left, right, strict=True))


def _l2_normalize(*, vector: list[float]) -> list[float]:
    """Normalize a vector by L2 magnitude.

    :param vector: Raw vector.
    :return: Normalized vector.
    """
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]
