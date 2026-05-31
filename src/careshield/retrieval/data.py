from careshield import contracts

DOCUMENTS = [
    contracts.schema.Document(
        id="clinical-access-policy",
        title="Clinical Access Policy",
        sensitivity=contracts.schema.Sensitivity.clinical,
        allowed_roles=[
            contracts.schema.Role.doctor,
            contracts.schema.Role.nurse,
            contracts.schema.Role.compliance_officer,
        ],
        tags=["clinical", "discharge", "care-team", "minimum-necessary"],
        body=(
            "Doctors and nurses may access discharge notes only for active patient care. "
            "Clinical notes must not be shared with external vendors unless the content is "
            "de-identified, minimum-necessary, and approved by compliance."
        ),
    ),
    contracts.schema.Document(
        id="patient-summary-redaction-guide",
        title="Patient Summary Redaction Guide",
        sensitivity=contracts.schema.Sensitivity.internal,
        allowed_roles=[
            contracts.schema.Role.doctor,
            contracts.schema.Role.nurse,
            contracts.schema.Role.vendor_manager,
            contracts.schema.Role.compliance_officer,
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
    contracts.schema.Document(
        id="billing-data-policy",
        title="Billing Data Policy",
        sensitivity=contracts.schema.Sensitivity.billing,
        allowed_roles=[contracts.schema.Role.billing_analyst, contracts.schema.Role.compliance_officer],
        tags=["billing", "insurance", "claims", "payment"],
        body=(
            "Billing analysts may access insurance identifiers and claim status for payment "
            "operations. They must not access full clinical notes unless a compliance officer "
            "approves a specific investigation."
        ),
    ),
    contracts.schema.Document(
        id="vendor-data-sharing-policy",
        title="Vendor Data Sharing Policy",
        sensitivity=contracts.schema.Sensitivity.internal,
        allowed_roles=[contracts.schema.Role.vendor_manager, contracts.schema.Role.compliance_officer],
        tags=["vendor", "sharing", "approval", "de-identification"],
        body=(
            "Vendor managers may coordinate approved vendor data exchanges. External sharing "
            "requires a business purpose, de-identification, a data processing agreement, and "
            "an audit trail. Raw PHI must not be sent to vendors."
        ),
    ),
    contracts.schema.Document(
        id="vendor-safe-summary",
        title="Vendor Safe Summary",
        sensitivity=contracts.schema.Sensitivity.public,
        allowed_roles=[
            contracts.schema.Role.external_vendor,
            contracts.schema.Role.vendor_manager,
            contracts.schema.Role.compliance_officer,
        ],
        tags=["vendor", "public", "safe-summary"],
        body=(
            "External vendors may receive only approved, de-identified, minimum-necessary "
            "summaries. Direct patient identifiers, medical record numbers, contact details, "
            "insurance identifiers, and diagnosis details are not allowed in vendor-facing data."
        ),
    ),
    contracts.schema.Document(
        id="model-use-policy",
        title="Model Use Policy",
        sensitivity=contracts.schema.Sensitivity.internal,
        allowed_roles=[
            contracts.schema.Role.doctor,
            contracts.schema.Role.nurse,
            contracts.schema.Role.billing_analyst,
            contracts.schema.Role.vendor_manager,
            contracts.schema.Role.compliance_officer,
        ],
        tags=["genai", "model-gateway", "public-api", "approved-provider"],
        body=(
            "Protected health information and internal healthcare documents must not be sent "
            "to public model APIs. Teams must use the approved model gateway, which enforces "
            "policy checks, redaction, audit logging, and structured response validation."
        ),
    ),
]
