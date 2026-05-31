import typing
import uuid

import chromadb
import chromadb.config

from careshield import contracts, guardrails, retrieval


class ChromaVectorStore:
    """Chroma-backed vector store for local learning and experiments."""

    def __init__(
        self,
        *,
        embedding_model: retrieval.embeddings.HashEmbeddingModel | None = None,
        collection_name: str | None = None,
    ) -> None:
        """Create an ephemeral Chroma collection.

        :param embedding_model: Embedding adapter used to vectorize text.
        :param collection_name: Optional Chroma collection name.
        """
        self.embedding_model = embedding_model or retrieval.embeddings.HashEmbeddingModel()
        self._documents_by_id: dict[str, contracts.schema.Document] = {}
        safe_name = collection_name or f"careshield-{uuid.uuid4().hex[:12]}"
        settings = chromadb.config.Settings(anonymized_telemetry=False)

        # Ephemeral Chroma keeps the repository simple: real vector DB behavior
        # without requiring a service or persistent local state.
        self._client: typing.Any = chromadb.EphemeralClient(settings=settings)
        self._collection: typing.Any = self._client.get_or_create_collection(name=safe_name)

    @property
    def size(self) -> int:
        """Return the number of indexed vectors.

        :return: Indexed vector count.
        """
        return len(self._documents_by_id)

    def add_documents(self, *, documents: list[contracts.schema.Document]) -> None:
        """Embed and store document chunks in Chroma.

        :param documents: Documents or chunks to index.
        """
        if not documents:
            return

        ids = [document.id for document in documents]
        self._collection.add(
            ids=ids,
            documents=[document.body for document in documents],
            embeddings=[
                self.embedding_model.embed(text=_document_text(document=document)) for document in documents
            ],
            metadatas=[_metadata_from_document(document=document) for document in documents],
        )
        self._documents_by_id.update({document.id: document for document in documents})

    def search(
        self,
        *,
        query: str,
        context: contracts.schema.UserContext,
        max_docs: int = 3,
    ) -> list[contracts.schema.Document]:
        """Search Chroma with a role metadata filter.

        :param query: User question.
        :param context: User role and purpose.
        :param max_docs: Maximum chunks to return.
        :return: Authorized chunks ranked by vector similarity.
        """
        if self.size == 0:
            return []

        result_count = min(max_docs, self.size)
        where_filter = _where_filter_from_context(context=context)
        result = self._collection.query(
            query_embeddings=[self.embedding_model.embed(text=query)],
            n_results=result_count,
            where=where_filter,
        )
        ids = typing.cast(list[str], result.get("ids", [[]])[0])
        metadatas = typing.cast(list[dict[str, object]], result.get("metadatas", [[]])[0])
        documents = typing.cast(list[str], result.get("documents", [[]])[0])

        # Apply the Python policy check as a second guard around the Chroma
        # metadata filter before anything can become prompt evidence.
        documents_from_chroma = [
            self._documents_by_id.get(doc_id)
            or _document_from_chroma_result(
                doc_id=doc_id,
                body=documents[index] or "",
                metadata=metadatas[index] or {},
            )
            for index, doc_id in enumerate(ids)
        ]
        allowed_documents = guardrails.policy.filter_allowed_documents(
            context=context,
            documents=documents_from_chroma,
        )
        return allowed_documents[:max_docs]


def _where_filter_from_context(*, context: contracts.schema.UserContext) -> dict[str, object]:
    """Build a Chroma metadata filter from the caller context.

    :param context: User role and purpose.
    :return: Chroma ``where`` filter for role and sensitivity.
    """
    allowed_sensitivities = [
        sensitivity.value for sensitivity in guardrails.policy.ROLE_SENSITIVITY_ALLOWLIST[context.role]
    ]

    # Chroma gets the same policy metadata as the Python filter, so the vector
    # search itself can avoid returning obviously unauthorized chunks.
    return {
        "$and": [
            {f"role_{context.role.value}": True},
            {"sensitivity": {"$in": allowed_sensitivities}},
        ]
    }


def _metadata_from_document(*, document: contracts.schema.Document) -> dict[str, str | bool]:
    """Convert a document into Chroma-compatible metadata.

    :param document: Document or chunk to index.
    :return: Metadata with role flags for pre-retrieval filtering.
    """
    metadata: dict[str, str | bool] = {
        "doc_id": document.id,
        "title": document.title,
        "sensitivity": document.sensitivity.value,
        "tags": ",".join(document.tags),
    }
    for role in contracts.schema.Role:
        metadata[f"role_{role.value}"] = role in document.allowed_roles
    return metadata


def _document_from_chroma_result(
    *,
    doc_id: str,
    body: str,
    metadata: dict[str, object],
) -> contracts.schema.Document:
    """Rebuild a document from Chroma query output.

    :param doc_id: Chroma result ID.
    :param body: Stored document text.
    :param metadata: Stored document metadata.
    :return: Document model.
    """
    allowed_roles = [role for role in contracts.schema.Role if bool(metadata.get(f"role_{role.value}"))]
    tags = str(metadata.get("tags", "")).split(",") if metadata.get("tags") else []
    sensitivity = str(metadata.get("sensitivity", contracts.schema.Sensitivity.internal.value))
    return contracts.schema.Document(
        id=str(metadata.get("doc_id", doc_id)),
        title=str(metadata.get("title", doc_id)),
        body=body,
        sensitivity=contracts.schema.Sensitivity(sensitivity),
        allowed_roles=allowed_roles,
        tags=tags,
    )


def _document_text(*, document: contracts.schema.Document) -> str:
    """Build the text used for embedding a document.

    :param document: Document or chunk to embed.
    :return: Combined title, body, and tags.
    """
    return " ".join([document.title, document.body, " ".join(document.tags)])
