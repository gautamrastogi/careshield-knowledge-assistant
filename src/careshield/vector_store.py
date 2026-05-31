from __future__ import annotations

from dataclasses import dataclass

from careshield.embeddings import HashEmbeddingModel, cosine_similarity
from careshield.policy import filter_allowed_documents
from careshield.schemas import Document, UserContext


@dataclass(frozen=True)
class VectorRecord:
    document: Document
    vector: list[float]


class InMemoryVectorStore:
    """Tiny vector DB adapter used by the demo and tests.

    The interface is intentionally close to a production vector store:
    documents are embedded at ingestion time, stored as vectors with metadata,
    and filtered by policy before similarity ranking.
    """

    def __init__(self, embedding_model: HashEmbeddingModel | None = None) -> None:
        self.embedding_model = embedding_model or HashEmbeddingModel()
        self._records: list[VectorRecord] = []

    @property
    def size(self) -> int:
        return len(self._records)

    def add_documents(self, documents: list[Document]) -> None:
        self._records.extend(
            VectorRecord(
                document=document,
                vector=self.embedding_model.embed(_document_text(document)),
            )
            for document in documents
        )

    def search(self, query: str, context: UserContext, max_docs: int = 3) -> list[Document]:
        allowed_ids = {
            document.id
            for document in filter_allowed_documents(context, [record.document for record in self._records])
        }
        query_vector = self.embedding_model.embed(query)
        scored = [
            (cosine_similarity(query_vector, record.vector), record.document)
            for record in self._records
            if record.document.id in allowed_ids
        ]
        scored.sort(key=lambda item: (item[0], item[1].title), reverse=True)
        return [document for score, document in scored if score > 0][:max_docs]


def _document_text(document: Document) -> str:
    return " ".join([document.title, document.body, " ".join(document.tags)])
