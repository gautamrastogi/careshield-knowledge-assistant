import re

import careshield.contracts.schemas as schemas
import careshield.guardrails.policy as policy


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


def tokenize(*, text: str) -> set[str]:
    """Convert text into normalized retrieval terms.

    :param text: Text to tokenize.
    :return: Lowercase non-stopword terms.
    """
    tokens = set(re.findall(pattern=r"[a-z0-9]+", string=text.lower()))
    return {token for token in tokens if token not in STOP_WORDS and len(token) > 2}


def score_document(*, question: str, document: schemas.Document) -> int:
    """Score a document using deterministic keyword overlap.

    :param question: User question.
    :param document: Candidate document.
    :return: Number of overlapping normalized terms.
    """
    question_terms = tokenize(text=question)
    doc_terms = tokenize(text=" ".join([document.title, document.body, " ".join(document.tags)]))
    return len(question_terms & doc_terms)


def retrieve(
    *,
    question: str,
    context: schemas.UserContext,
    documents: list[schemas.Document],
    max_docs: int = 3,
) -> list[schemas.Document]:
    """Retrieve authorized built-in documents.

    :param question: User question.
    :param context: User role and purpose.
    :param documents: Candidate policy documents.
    :param max_docs: Maximum documents to return.
    :return: Relevant documents after policy filtering and ranking.
    """
    allowed_documents = policy.filter_allowed_documents(context=context, documents=documents)
    scored = [
        (score_document(question=question, document=document), document)
        for document in allowed_documents
    ]
    scored.sort(key=lambda item: (item[0], item[1].title), reverse=True)
    relevant = [document for score, document in scored if score > 0]
    return relevant[:max_docs]


def to_evidence(*, document: schemas.Document, quote: str) -> schemas.Evidence:
    """Convert a retrieved document into a response citation.

    :param document: Retrieved document or chunk.
    :param quote: Redacted quote selected from the document body.
    :return: Citation object for the API response.
    """
    return schemas.Evidence(
        doc_id=document.id,
        title=document.title,
        quote=quote,
        sensitivity=document.sensitivity,
    )
