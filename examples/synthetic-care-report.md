# Synthetic Care Coordination Report

This sample document is synthetic and safe for public demos.

Care teams may summarize a discharge plan for approved follow-up providers.
Before sharing outside the organization, the summary must be de-identified and
limited to the minimum necessary operational context.

Do not include patient names, phone numbers, email addresses, medical record
numbers, insurance identifiers, or diagnosis details unless a compliance
approval explicitly authorizes the disclosure.

Synthetic unsafe example for redaction testing: Patient Jane Example,
jane.example@example.invalid, +1-555-0100, MRN MRN-000-EXAMPLE,
Insurance ID INS-000-EXAMPLE, diagnosis Type 2 diabetes.

The approved GenAI workflow is to parse the document, split it into chunks,
embed those chunks, filter retrieval by user role and document sensitivity,
redact sensitive identifiers, call the approved model gateway, validate the
structured answer, and run citation, grounding, policy, and PII checks before
returning the result.
