from __future__ import annotations

import re

from careshield.policy import filter_allowed_documents
from careshield.schemas import Document, Evidence, UserContext


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "for",
    "from",
    "how",
    "i",
    "is",
    "it",
    "of",
    "or",
    "the",
    "to",
    "what",
    "when",
    "which",
    "with",
}


def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    return {token for token in tokens if token not in STOP_WORDS and len(token) > 2}


def score_document(question: str, document: Document) -> int:
    question_terms = tokenize(question)
    doc_terms = tokenize(" ".join([document.title, document.body, " ".join(document.tags)]))
    return len(question_terms & doc_terms)


def retrieve(
    question: str,
    context: UserContext,
    documents: list[Document],
    max_docs: int = 3,
) -> list[Document]:
    allowed_documents = filter_allowed_documents(context, documents)
    scored = [
        (score_document(question, document), document)
        for document in allowed_documents
    ]
    scored.sort(key=lambda item: (item[0], item[1].title), reverse=True)
    relevant = [document for score, document in scored if score > 0]
    return relevant[:max_docs]


def to_evidence(document: Document, quote: str) -> Evidence:
    return Evidence(
        doc_id=document.id,
        title=document.title,
        quote=quote,
        sensitivity=document.sensitivity,
    )
