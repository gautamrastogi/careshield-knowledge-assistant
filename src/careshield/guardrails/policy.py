import careshield.contracts.schemas as schemas


ROLE_SENSITIVITY_ALLOWLIST: dict[schemas.Role, set[schemas.Sensitivity]] = {
    schemas.Role.doctor: {
        schemas.Sensitivity.public,
        schemas.Sensitivity.internal,
        schemas.Sensitivity.clinical,
    },
    schemas.Role.nurse: {
        schemas.Sensitivity.public,
        schemas.Sensitivity.internal,
        schemas.Sensitivity.clinical,
    },
    schemas.Role.billing_analyst: {
        schemas.Sensitivity.public,
        schemas.Sensitivity.internal,
        schemas.Sensitivity.billing,
    },
    schemas.Role.vendor_manager: {schemas.Sensitivity.public, schemas.Sensitivity.internal},
    schemas.Role.external_vendor: {schemas.Sensitivity.public},
    schemas.Role.compliance_officer: {
        schemas.Sensitivity.public,
        schemas.Sensitivity.internal,
        schemas.Sensitivity.clinical,
        schemas.Sensitivity.billing,
        schemas.Sensitivity.restricted,
    },
}


def can_access(*, context: schemas.UserContext, document: schemas.Document) -> bool:
    """Return whether the caller can use a document as prompt evidence.

    :param context: User role and purpose derived from the request.
    :param document: Document or chunk being considered for retrieval.
    :return: Whether the document is allowed for this caller.
    """
    allowed_sensitivities = ROLE_SENSITIVITY_ALLOWLIST[context.role]
    return document.sensitivity in allowed_sensitivities and context.role in set(document.allowed_roles)


def filter_allowed_documents(
    *,
    context: schemas.UserContext,
    documents: list[schemas.Document],
) -> list[schemas.Document]:
    """Filter documents before retrieval ranking.

    :param context: User role and purpose derived from the request.
    :param documents: Candidate documents or chunks.
    :return: Documents the caller is allowed to use.
    """
    return [document for document in documents if can_access(context=context, document=document)]
