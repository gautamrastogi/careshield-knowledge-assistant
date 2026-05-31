import careshield.contracts.schemas as schemas


DOCUMENTS = [
    schemas.Document(
        id="clinical-access-policy",
        title="Clinical Access Policy",
        sensitivity=schemas.Sensitivity.clinical,
        allowed_roles=[schemas.Role.doctor, schemas.Role.nurse, schemas.Role.compliance_officer],
        tags=["clinical", "discharge", "care-team", "minimum-necessary"],
        body=(
            "Doctors and nurses may access discharge notes only for active patient care. "
            "Clinical notes must not be shared with external vendors unless the content is "
            "de-identified, minimum-necessary, and approved by compliance."
        ),
    ),
    schemas.Document(
        id="patient-summary-redaction-guide",
        title="Patient Summary Redaction Guide",
        sensitivity=schemas.Sensitivity.internal,
        allowed_roles=[
            schemas.Role.doctor,
            schemas.Role.nurse,
            schemas.Role.vendor_manager,
            schemas.Role.compliance_officer,
        ],
        tags=["redaction", "phi", "pii", "vendor-sharing"],
        body=(
            "Before a patient summary is sent outside the organization, redact patient name, "
            "email, phone, medical record number, insurance id, and diagnosis details unless "
            "a specific compliance approval says otherwise. Synthetic example: Patient Jane "
            "Example, email jane.example@example.invalid, phone +1-555-0100, MRN MRN-000-EXAMPLE, "
            "Insurance ID INS-000-EXAMPLE, diagnosis Type 2 diabetes."
        ),
    ),
    schemas.Document(
        id="billing-data-policy",
        title="Billing Data Policy",
        sensitivity=schemas.Sensitivity.billing,
        allowed_roles=[schemas.Role.billing_analyst, schemas.Role.compliance_officer],
        tags=["billing", "insurance", "claims", "payment"],
        body=(
            "Billing analysts may access insurance identifiers and claim status for payment "
            "operations. They must not access full clinical notes unless a compliance officer "
            "approves a specific investigation."
        ),
    ),
    schemas.Document(
        id="vendor-data-sharing-policy",
        title="Vendor Data Sharing Policy",
        sensitivity=schemas.Sensitivity.internal,
        allowed_roles=[schemas.Role.vendor_manager, schemas.Role.compliance_officer],
        tags=["vendor", "sharing", "approval", "de-identification"],
        body=(
            "Vendor managers may coordinate approved vendor data exchanges. External sharing "
            "requires a business purpose, de-identification, a data processing agreement, and "
            "an audit trail. Raw PHI must not be sent to vendors."
        ),
    ),
    schemas.Document(
        id="vendor-safe-summary",
        title="Vendor Safe Summary",
        sensitivity=schemas.Sensitivity.public,
        allowed_roles=[
            schemas.Role.external_vendor,
            schemas.Role.vendor_manager,
            schemas.Role.compliance_officer,
        ],
        tags=["vendor", "public", "safe-summary"],
        body=(
            "External vendors may receive only approved, de-identified, minimum-necessary "
            "summaries. Direct patient identifiers, medical record numbers, contact details, "
            "insurance identifiers, and diagnosis details are not allowed in vendor-facing data."
        ),
    ),
    schemas.Document(
        id="model-use-policy",
        title="Model Use Policy",
        sensitivity=schemas.Sensitivity.internal,
        allowed_roles=[
            schemas.Role.doctor,
            schemas.Role.nurse,
            schemas.Role.billing_analyst,
            schemas.Role.vendor_manager,
            schemas.Role.compliance_officer,
        ],
        tags=["genai", "model-gateway", "public-api", "approved-provider"],
        body=(
            "Protected health information and internal healthcare documents must not be sent "
            "to public model APIs. Teams must use the approved model gateway, which enforces "
            "policy checks, redaction, audit logging, and structured response validation."
        ),
    ),
]
