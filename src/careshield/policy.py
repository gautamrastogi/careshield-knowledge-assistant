from __future__ import annotations

from careshield.schemas import Document, Role, Sensitivity, UserContext


ROLE_SENSITIVITY_ALLOWLIST: dict[Role, set[Sensitivity]] = {
    Role.doctor: {Sensitivity.public, Sensitivity.internal, Sensitivity.clinical},
    Role.nurse: {Sensitivity.public, Sensitivity.internal, Sensitivity.clinical},
    Role.billing_analyst: {Sensitivity.public, Sensitivity.internal, Sensitivity.billing},
    Role.vendor_manager: {Sensitivity.public, Sensitivity.internal},
    Role.external_vendor: {Sensitivity.public},
    Role.compliance_officer: {
        Sensitivity.public,
        Sensitivity.internal,
        Sensitivity.clinical,
        Sensitivity.billing,
        Sensitivity.restricted,
    },
}


def can_access(context: UserContext, document: Document) -> bool:
    allowed_sensitivities = ROLE_SENSITIVITY_ALLOWLIST[context.role]
    return (
        document.sensitivity in allowed_sensitivities
        and context.role in set(document.allowed_roles)
    )


def filter_allowed_documents(
    context: UserContext,
    documents: list[Document],
) -> list[Document]:
    return [document for document in documents if can_access(context, document)]
