import typing

import pydantic

from careshield import contracts, guardrails, retrieval


class VectorRecord(pydantic.BaseModel):
    """Stored vector and its source document metadata."""

    model_config = pydantic.ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "document": {
                        "id": "synthetic-care-report-chunk-1",
                        "title": "synthetic-care-report section 1",
                        "body": "Vendor sharing requires redaction.",
                        "sensitivity": "clinical",
                        "allowed_roles": ["nurse"],
                        "tags": ["uploaded-report"],
                    },
                    "vector": [0.1, 0.2, 0.3],
                }
            ]
        },
    )

    document: contracts.schema.Document
    vector: list[float] = pydantic.Field(min_length=1)


class VectorStore(typing.Protocol):
    """Common interface for vector store implementations."""

    @property
    def size(self) -> int:
        """Return the number of indexed vectors.

        :return: Indexed vector count.
        """
        raise NotImplementedError

    def add_documents(self, *, documents: list[contracts.schema.Document]) -> None:
        """Index document chunks.

        :param documents: Documents or chunks to index.
        """
        raise NotImplementedError

    def search(
        self,
        *,
        query: str,
        context: contracts.schema.UserContext,
        max_docs: int = 3,
    ) -> list[contracts.schema.Document]:
        """Search authorized chunks.

        :param query: User question.
        :param context: User role and purpose.
        :param max_docs: Maximum chunks to return.
        :return: Authorized chunks ranked by relevance.
        """
        raise NotImplementedError


class InMemoryVectorStore:
    """Tiny vector DB adapter used by the demo and tests."""

    def __init__(self, *, embedding_model: retrieval.embeddings.HashEmbeddingModel | None = None) -> None:
        """Create a local vector store.

        :param embedding_model: Embedding adapter used to vectorize text.
        """
        self.embedding_model = embedding_model or retrieval.embeddings.HashEmbeddingModel()
        self._records: list[VectorRecord] = []

    @property
    def size(self) -> int:
        """Return the number of indexed vectors.

        :return: Indexed vector count.
        """
        return len(self._records)

    def add_documents(self, *, documents: list[contracts.schema.Document]) -> None:
        """Embed and store document chunks.

        :param documents: Documents or chunks to index.
        """
        self._records.extend(
            VectorRecord(
                document=document,
                vector=self.embedding_model.embed(text=_document_text(document=document)),
            )
            for document in documents
        )

    def search(
        self,
        *,
        query: str,
        context: contracts.schema.UserContext,
        max_docs: int = 3,
    ) -> list[contracts.schema.Document]:
        """Search vectors after applying role/sensitivity filtering.

        :param query: User question.
        :param context: User role and purpose.
        :param max_docs: Maximum chunks to return.
        :return: Authorized chunks ranked by vector similarity.
        """
        allowed_ids = {
            document.id
            for document in guardrails.policy.filter_allowed_documents(
                context=context,
                documents=[record.document for record in self._records],
            )
        }
        query_vector = self.embedding_model.embed(text=query)

        # The policy filter runs before ranking, so unauthorized chunks never
        # become prompt evidence even if they are semantically similar.
        scored = [
            (
                retrieval.embeddings.cosine_similarity(left=query_vector, right=record.vector),
                record.document,
            )
            for record in self._records
            if record.document.id in allowed_ids
        ]
        scored.sort(key=lambda item: (item[0], item[1].title), reverse=True)
        return [document for score, document in scored if score > 0][:max_docs]


def _document_text(*, document: contracts.schema.Document) -> str:
    """Build the text used for embedding a document.

    :param document: Document or chunk to embed.
    :return: Combined title, body, and tags.
    """
    return " ".join([document.title, document.body, " ".join(document.tags)])


def build_vector_store(
    *,
    backend: str,
    embedding_model: retrieval.embeddings.HashEmbeddingModel,
) -> VectorStore:
    """Create a vector store implementation by name.

    :param backend: Vector backend name: ``memory`` or ``chroma``.
    :param embedding_model: Embedding adapter used by the vector store.
    :return: Vector store implementation.
    """
    if backend == "memory":
        return InMemoryVectorStore(embedding_model=embedding_model)
    if backend == "chroma":
        from careshield.retrieval import chroma_store

        return chroma_store.ChromaVectorStore(embedding_model=embedding_model)
    raise ValueError(f"unsupported vector store backend: {backend}")
