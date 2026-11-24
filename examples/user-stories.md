# Example user stories

These inputs are fixtures. They are not model output. Paste one into New generation while the provider is set to Mock.

## Transfer between accounts

Kind: user story

```text
As a customer, I want to transfer money between my accounts so that I can pay a bill.

Acceptance criteria:
1. The customer can transfer an amount between 0.01 and 10000 USD in a single transaction.
2. A transfer that exceeds the daily limit of 25000 USD is rejected with an error.
3. A successful transfer shows a confirmation number.
4. Insufficient funds show an error and do not change the balance.
```

What the analyzer should surface:

- Actor: customer (extracted)
- Four acceptance criteria (extracted)
- Numeric constraints for 0.01, 10000, and 25000 (extracted)
- A gap for authentication, because the story never says how the customer signs in (inferred)

## Ambiguous dashboard request

Kind: user story

```text
As a user, I want the dashboard to load fast and feel user-friendly.
Acceptance criteria:
1. The page should be intuitive.
2. Exact fields are TBD.
```

The ambiguity list quotes the sentences that contain "fast", "user-friendly", "intuitive", and "TBD". Those quotes are in the source. The label itself comes from a fixed term list.

## Invoice approval

Kind: requirements document

```text
Requirements document: Invoice approval

Actors:
- Clerk submits an invoice.
- Manager approves or rejects it.

The system shall allow a manager to approve an invoice only if the amount is at most 5000 USD.
The system shall reject an invoice when a required field is missing.
Given a submitted invoice, when a manager approves it, then the clerk sees status Approved.
The workflow depends on the notification service.
```

Expect extracted actors, a business rule, a dependency on the notification service, and one Given/When/Then criterion.
