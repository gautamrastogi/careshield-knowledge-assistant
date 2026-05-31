from careshield import contracts

ROLE_SENSITIVITY_ALLOWLIST: dict[contracts.schema.Role, set[contracts.schema.Sensitivity]] = {
    contracts.schema.Role.doctor: {
        contracts.schema.Sensitivity.public,
        contracts.schema.Sensitivity.internal,
        contracts.schema.Sensitivity.clinical,
    },
    contracts.schema.Role.nurse: {
        contracts.schema.Sensitivity.public,
        contracts.schema.Sensitivity.internal,
        contracts.schema.Sensitivity.clinical,
    },
    contracts.schema.Role.billing_analyst: {
        contracts.schema.Sensitivity.public,
        contracts.schema.Sensitivity.internal,
        contracts.schema.Sensitivity.billing,
    },
    contracts.schema.Role.vendor_manager: {
        contracts.schema.Sensitivity.public,
        contracts.schema.Sensitivity.internal,
    },
    contracts.schema.Role.external_vendor: {contracts.schema.Sensitivity.public},
    contracts.schema.Role.compliance_officer: {
        contracts.schema.Sensitivity.public,
        contracts.schema.Sensitivity.internal,
        contracts.schema.Sensitivity.clinical,
        contracts.schema.Sensitivity.billing,
        contracts.schema.Sensitivity.restricted,
    },
}


def can_access(*, context: contracts.schema.UserContext, document: contracts.schema.Document) -> bool:
    """Return whether the caller can use a document as prompt evidence.

    :param context: User role and purpose derived from the request.
    :param document: Document or chunk being considered for retrieval.
    :return: Whether the document is allowed for this caller.
    """
    allowed_sensitivities = ROLE_SENSITIVITY_ALLOWLIST[context.role]
    return document.sensitivity in allowed_sensitivities and context.role in set(document.allowed_roles)


def filter_allowed_documents(
    *,
    context: contracts.schema.UserContext,
    documents: list[contracts.schema.Document],
) -> list[contracts.schema.Document]:
    """Filter documents before retrieval ranking.

    :param context: User role and purpose derived from the request.
    :param documents: Candidate documents or chunks.
    :return: Documents the caller is allowed to use.
    """
    return [document for document in documents if can_access(context=context, document=document)]
