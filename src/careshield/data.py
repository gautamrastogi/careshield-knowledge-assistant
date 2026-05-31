from __future__ import annotations

from careshield.schemas import Document, Role, Sensitivity


DOCUMENTS = [
    Document(
        id="clinical-access-policy",
        title="Clinical Access Policy",
        sensitivity=Sensitivity.clinical,
        allowed_roles=[Role.doctor, Role.nurse, Role.compliance_officer],
        tags=["clinical", "discharge", "care-team", "minimum-necessary"],
        body=(
            "Doctors and nurses may access discharge notes only for active patient care. "
            "Clinical notes must not be shared with external vendors unless the content is "
            "de-identified, minimum-necessary, and approved by compliance."
        ),
    ),
    Document(
        id="patient-summary-redaction-guide",
        title="Patient Summary Redaction Guide",
        sensitivity=Sensitivity.internal,
        allowed_roles=[Role.doctor, Role.nurse, Role.vendor_manager, Role.compliance_officer],
        tags=["redaction", "phi", "pii", "vendor-sharing"],
        body=(
            "Before a patient summary is sent outside the organization, redact patient name, "
            "email, phone, medical record number, insurance id, and diagnosis details unless "
            "a specific compliance approval says otherwise. Synthetic example: Patient Jane "
            "Example, email jane.example@example.invalid, phone +1-555-0100, MRN MRN-000-EXAMPLE, "
            "Insurance ID INS-000-EXAMPLE, diagnosis Type 2 diabetes."
        ),
    ),
    Document(
        id="billing-data-policy",
        title="Billing Data Policy",
        sensitivity=Sensitivity.billing,
        allowed_roles=[Role.billing_analyst, Role.compliance_officer],
        tags=["billing", "insurance", "claims", "payment"],
        body=(
            "Billing analysts may access insurance identifiers and claim status for payment "
            "operations. They must not access full clinical notes unless a compliance officer "
            "approves a specific investigation."
        ),
    ),
    Document(
        id="vendor-data-sharing-policy",
        title="Vendor Data Sharing Policy",
        sensitivity=Sensitivity.internal,
        allowed_roles=[Role.vendor_manager, Role.compliance_officer],
        tags=["vendor", "sharing", "approval", "de-identification"],
        body=(
            "Vendor managers may coordinate approved vendor data exchanges. External sharing "
            "requires a business purpose, de-identification, a data processing agreement, and "
            "an audit trail. Raw PHI must not be sent to vendors."
        ),
    ),
    Document(
        id="vendor-safe-summary",
        title="Vendor Safe Summary",
        sensitivity=Sensitivity.public,
        allowed_roles=[Role.external_vendor, Role.vendor_manager, Role.compliance_officer],
        tags=["vendor", "public", "safe-summary"],
        body=(
            "External vendors may receive only approved, de-identified, minimum-necessary "
            "summaries. Direct patient identifiers, medical record numbers, contact details, "
            "insurance identifiers, and diagnosis details are not allowed in vendor-facing data."
        ),
    ),
    Document(
        id="model-use-policy",
        title="Model Use Policy",
        sensitivity=Sensitivity.internal,
        allowed_roles=[
            Role.doctor,
            Role.nurse,
            Role.billing_analyst,
            Role.vendor_manager,
            Role.compliance_officer,
        ],
        tags=["genai", "model-gateway", "public-api", "approved-provider"],
        body=(
            "Protected health information and internal healthcare documents must not be sent "
            "to public model APIs. Teams must use the approved model gateway, which enforces "
            "policy checks, redaction, audit logging, and structured response validation."
        ),
    ),
]
