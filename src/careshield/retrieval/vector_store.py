import dataclasses

import careshield.contracts.schemas as schemas
import careshield.guardrails.policy as policy
import careshield.retrieval.embeddings as embeddings


@dataclasses.dataclass(frozen=True)
class VectorRecord:
    """Stored vector and its source document metadata."""

    document: schemas.Document
    vector: list[float]


class InMemoryVectorStore:
    """Tiny vector DB adapter used by the demo and tests."""

    def __init__(self, *, embedding_model: embeddings.HashEmbeddingModel | None = None) -> None:
        """Create a local vector store.

        :param embedding_model: Embedding adapter used to vectorize text.
        """
        self.embedding_model = embedding_model or embeddings.HashEmbeddingModel()
        self._records: list[VectorRecord] = []

    @property
    def size(self) -> int:
        """Return the number of indexed vectors.

        :return: Indexed vector count.
        """
        return len(self._records)

    def add_documents(self, *, documents: list[schemas.Document]) -> None:
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
        context: schemas.UserContext,
        max_docs: int = 3,
    ) -> list[schemas.Document]:
        """Search vectors after applying role/sensitivity filtering.

        :param query: User question.
        :param context: User role and purpose.
        :param max_docs: Maximum chunks to return.
        :return: Authorized chunks ranked by vector similarity.
        """
        allowed_ids = {
            document.id
            for document in policy.filter_allowed_documents(
                context=context,
                documents=[record.document for record in self._records],
            )
        }
        query_vector = self.embedding_model.embed(text=query)

        # The policy filter runs before ranking, so unauthorized chunks never
        # become prompt evidence even if they are semantically similar.
        scored = [
            (
                embeddings.cosine_similarity(left=query_vector, right=record.vector),
                record.document,
            )
            for record in self._records
            if record.document.id in allowed_ids
        ]
        scored.sort(key=lambda item: (item[0], item[1].title), reverse=True)
        return [document for score, document in scored if score > 0][:max_docs]


def _document_text(*, document: schemas.Document) -> str:
    """Build the text used for embedding a document.

    :param document: Document or chunk to embed.
    :return: Combined title, body, and tags.
    """
    return " ".join([document.title, document.body, " ".join(document.tags)])
