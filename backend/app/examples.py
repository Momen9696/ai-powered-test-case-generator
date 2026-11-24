"""Example requirements shipped with the application.

These strings are fixtures for demos and tests. They are not model output.
"""

SAMPLE_TRANSFER_STORY = """As a customer, I want to transfer money between my accounts so that I can pay a bill.

Acceptance criteria:
1. The customer can transfer an amount between 0.01 and 10000 USD in a single transaction.
2. A transfer that exceeds the daily limit of 25000 USD is rejected with an error.
3. A successful transfer shows a confirmation number.
4. Insufficient funds show an error and do not change the balance.
"""

SAMPLE_AMBIGUOUS_STORY = """As a user, I want the dashboard to load fast and feel user-friendly.
Acceptance criteria:
1. The page should be intuitive.
2. Exact fields are TBD.
"""

SAMPLE_REQUIREMENTS_DOC = """Requirements document: Invoice approval

Actors:
- Clerk submits an invoice.
- Manager approves or rejects it.

The system shall allow a manager to approve an invoice only if the amount is at most 5000 USD.
The system shall reject an invoice when a required field is missing.
Given a submitted invoice, when a manager approves it, then the clerk sees status Approved.
The workflow depends on the notification service.
"""

EXAMPLES = {
    "transfer_user_story": {
        "title": "Transfer money between accounts",
        "kind": "user_story",
        "content": SAMPLE_TRANSFER_STORY.strip(),
        "note": "Demo input. Generating from it uses the configured provider. The default provider is the local mock.",
    },
    "ambiguous_user_story": {
        "title": "Ambiguous dashboard story",
        "kind": "user_story",
        "content": SAMPLE_AMBIGUOUS_STORY.strip(),
        "note": "Written to exercise ambiguity and missing-detail detection.",
    },
    "invoice_requirements": {
        "title": "Invoice approval requirements",
        "kind": "requirements_document",
        "content": SAMPLE_REQUIREMENTS_DOC.strip(),
        "note": "A short requirements document with actors, a business rule, and a dependency.",
    },
}
