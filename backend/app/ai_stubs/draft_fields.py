def missing_fields(doc_type: str, known_fields: dict) -> list[str]:
    """Later this will choose the most useful questions for a document draft."""
    # TODO: replace with real AI logic
    required = {"rti_application": ["applicant_name", "address", "public_authority", "information_requested"], "wage_complaint": ["complainant_name", "employer_name", "amount_due", "work_period"], "consumer_complaint": ["complainant_name", "seller_name", "issue", "relief_requested"], "legal_notice": ["sender_name", "recipient_name", "facts", "demand"]}
    return [field for field in required.get(doc_type, []) if not known_fields.get(field)]
