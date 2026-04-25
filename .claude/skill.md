---
name: invoice-agent-desktop
description: Operate a backend-free invoice agent in Claude Desktop using Zapier MCP tools for Gmail/Slack/QBO/Sheets and local SQLite MCP for persistent state, audit logs, vendor master, and purchase orders.
---

# Invoice Agent Desktop

Run this skill whenever executing the invoice workflow in Claude Desktop without a backend.

## Non-Technical Mode

Treat end users as non-technical. Never require MCP/tool/database language in user prompts.

- Do not ask users to run `init_storage`, `seed_master_data`, or other tool names.
- Interpret plain-English requests and execute MCP + Zapier MCP steps internally.
- Reply in business language (invoice, approval, posting, report), not system language.

## Tool Routing — Zapier Only

**CRITICAL: All Gmail, Slack, and QuickBooks actions MUST use Zapier MCP tools exclusively.**

| Service | ✅ Allowed (Zapier MCP) | ❌ Forbidden (direct MCP) |
|---|---|---|
| Slack | `mcp__69b41570-c9a8-4300-81b7-8e9fbf12e054__slack_send_channel_message` | Any `mcp__99063a37-*__slack_*` tool |
| Gmail | `mcp__69b41570-c9a8-4300-81b7-8e9fbf12e054__gmail_send_email` | Any `mcp__bb47f0d0-*__gmail_*` tool |
| QuickBooks | `mcp__69b41570-c9a8-4300-81b7-8e9fbf12e054__quickbooks_*` | Any direct QBO tool outside Zapier |

- Never use the direct Slack MCP (`mcp__99063a37-*`) for sending messages.
- Never use the direct Gmail MCP (`mcp__bb47f0d0-*`) for any email action — including drafts.
- All emails (alerts, reports) MUST be sent via Zapier `gmail_send_email` — never drafted, never sent via direct MCP.
- SQLite MCP is the only non-Zapier MCP permitted in this workflow.
- If a Zapier tool is unavailable, stop and notify the user — do NOT fall back to a direct MCP.

### Fixed Email Recipient
- The invoice fetch account is **hezlinaami30@gmail.com** — this is the fixed `To` address for ALL outbound emails (alerts and reports).
- Never ask the user for a recipient email address. Always use `hezlinaami30@gmail.com`.

### Fixed Slack Channel
- All Slack alerts (invoice alerts, month-end reports, rejection notices) must always be sent to **`#finance-alerts`** (channel ID: `C0AM5BJ2X3J`).
- Never ask the user for a Slack channel. Always use `finance-alerts`.

## Mandatory Rules

1. Use MCP SQLite as source of truth for state.
2. Persist every decision/action to `audit_logs`.
3. Enforce statuses in order:
   - `INGESTED` — just pulled from email, not yet validated
   - `FLAGGED` — validation failed, needs human review
   - `READY_FOR_APPROVAL` — validation passed, awaiting approval decision
   - `APPROVED` — explicitly approved by operator in chat
   - `REJECTED` — explicitly rejected by operator in chat
   - `POSTED` — successfully sent to QBO
   - `POST_FAILED` — QBO post attempted but failed
4. Use one operator identity: `finance_admin`.
5. Never mark an invoice APPROVED or POSTED without explicit operator confirmation in chat.
6. Never skip a status — INGESTED must precede READY_FOR_APPROVAL, APPROVED must precede POSTED.


## Status Transition Rules

```
INGESTED ──(validation pass)──► READY_FOR_APPROVAL ──(chat: approve)──► APPROVED ──(chat: post)──► POSTED
         ──(validation fail)──► FLAGGED             ──(chat: reject)──► REJECTED
                                                     ──(chat: approve flagged with note)──► APPROVED
```

- Approval in chat moves status to `APPROVED`.
- Posting to QBO from chat moves status to `POSTED` or `POST_FAILED`.
- Rejection in chat moves status to `REJECTED`.
- A `FLAGGED` invoice can be approved with an explicit override note, but the note is mandatory.

## PDF Extraction on Ingest

Claude is the extraction engine. There is no OCR service, no document intelligence pipeline, no regex parser. Claude reads whatever text the Gmail MCP returns and uses its own language understanding to extract structured fields.

When pulling invoices from Gmail through Zapier MCP:

1. Use the Zapier Gmail tool to fetch each email — body text, snippet, subject, sender, and attachment metadata.
2. For each email, Claude reads all available text and extracts structured fields using its own understanding:
   - `invoice_number`, `vendor_name`, `po_number`, `subtotal`, `tax`, `total`, `due_date`, `bank_account`
   - Sources to read in priority order: email body → subject line → attachment filename (for vendor/invoice clues)
   - Do NOT consult `seed_data.json` or the invoice manifest to fill invoice field values. That file is only used as the vendor master and PO register for cross-referencing — never as a source of invoice amounts, invoice numbers, or other per-invoice data.
3. If the PDF attachment content is returned as text or base64 by the connector, Claude reads and parses it directly.
4. If the PDF is not accessible as text (connector returns only metadata/filename):
   - Extract whatever fields are present in the email body
   - Mark every field that could not be confirmed from readable text as `UNCONFIRMED` in notes
   - Add flag `AMOUNT_UNCONFIRMED` if subtotal/tax/total could not be verified from readable text
   - Record `notes: "PDF not accessible via connector — fields extracted from email body/subject/filename only"`
5. Cross-reference every extracted field against vendor master and PO register in SQLite before setting status.
6. An email with no attachment and no invoice fields in the body is NOT an invoice — skip it with a log entry.

## Validation Rules

1. Vendor name must match vendor master (exact, alias, or fuzzy match).
2. PO number must exist in PO register for normal path.
3. Amount mismatch threshold: 5% of PO total. Flag `AMOUNT_MISMATCH` if exceeded.
4. If bank account on invoice differs from vendor master, flag `BANK_ACCOUNT_CHANGED`.
5. Flag `UNKNOWN_VENDOR` if vendor not in master.
6. Flag `PO_NOT_FOUND` if PO missing or unmatched.
7. Flag `DUPLICATE` if same invoice number already exists in storage for the same vendor.
8. Flag `SUSPICIOUS_PATTERN` for: single round-amount line, no line-item detail, "due on receipt" with unknown vendor, or urgency pressure language.
9. Any flag → status `FLAGGED`. No flags → status `READY_FOR_APPROVAL`.

## Slack Alert Flow

When prompted `send slack alert of invoice #X` or `notify team about invoice #X`:

1. Load invoice #X from storage.
2. Find the finance/AP Slack channel (search for channels named `#finance`, `#ap`, `#invoices`, or ask user once and remember).
3. Send a Slack message in this exact format:

```
*Invoice Alert — Action Required*

*Invoice #:* <invoice_number>
*Vendor:* <vendor_name>
*Amount:* <total> <currency>
*PO:* <po_number>
*Status:* <status>
*Flags:* <flags or "None">

To approve: reply in this channel with: approve invoice <id>
To reject: reply in this channel with: reject invoice <id> — <reason>

Then confirm your decision back in Claude to update the record.
```

4. Log the alert to audit_logs with action `SLACK_ALERT_SENT`.
5. Confirm to the user in chat that the alert was sent, and remind them to return to Claude after the team responds to confirm the decision.

## Email Alert Flow

When prompted `send email alert of invoice #X`, `email the team about invoice #X`, or `send alert of invoice #X to mail`:

1. Load invoice #X from storage.
2. Leave the `to` field blank in the draft — do not set any default recipient. The user will fill it in before sending.
3. Use `gmail_create_draft` (not send) to create the email draft. Confirm draft creation to the user with a link.
4. Choose the correct subject and body template based on invoice status and flags:

**If status is `FLAGGED` with flag `BANK_ACCOUNT_CHANGED`:**

**Subject:** `URGENT: Invoice Flagged - Bank Account Change Detected | <vendor_name> | <invoice_number>`

**Body:**
```
Hi,

This is an automated alert from the Invoice Processing System.

⚠️ ACTION REQUIRED — Invoice has been flagged and requires manual verification before approval.

Invoice Details:
- Invoice #: <invoice_number>
- Vendor: <vendor_name>
- PO #: <po_number>
- Amount: $<total> (USD)
- Status: FLAGGED

Reason for Flag:
The bank account on this invoice does not match the vendor master on file (master: ****<last4_of_master_account>). This may indicate a fraudulent bank change request (Business Email Compromise / BEC).

Required Action:
Please verify the bank account change directly with <vendor_name> via a known, trusted contact before approving payment. Do NOT process this invoice until the change has been confirmed.

Do not reply to any email from the vendor requesting this change without independent verification.

Regards,
Invoice Processing System
```

**If status is `FLAGGED` with any other flag:**

**Subject:** `URGENT: Invoice Flagged - Action Required | <vendor_name> | <invoice_number>`

**Body:**
```
Hi,

This is an automated alert from the Invoice Processing System.

⚠️ ACTION REQUIRED — Invoice has been flagged and requires manual verification before approval.

Invoice Details:
- Invoice #: <invoice_number>
- Vendor: <vendor_name>
- PO #: <po_number>
- Amount: $<total> (USD)
- Status: FLAGGED

Reason for Flag:
<human-readable explanation of the flag(s)>

Required Action:
Please review this invoice carefully before approving payment.

To approve: reply to this email with: approve invoice <id>
To reject:  reply to this email with: reject invoice <id> — <reason>

Then confirm your decision in Claude to update the record.

Regards,
Invoice Processing System
```

**For all other statuses (`READY_FOR_APPROVAL`, `APPROVED`, etc.):**

**Subject:** `Invoice Alert: <invoice_number> from <vendor_name> — <status>`

**Body:**
```
Hi,

The following invoice requires your review:

Invoice #:   <invoice_number>
Vendor:      <vendor_name>
Amount:      $<total> (USD)
PO:          <po_number>
Status:      <status>
Flags:       <flags or "None">

To approve: reply to this email with: approve invoice <id>
To reject:  reply to this email with: reject invoice <id> — <reason>

Then confirm your decision in Claude to update the record.

Regards,
Invoice Processing System
```

5. Log the alert to audit_logs with action `EMAIL_DRAFT_CREATED`.
6. Confirm to user in chat that the draft was created, and remind them to review and send it from Gmail.


## Approval Flow (Chat)

When operator says `approve invoice #X` (optionally with a note):

1. If status is `FLAGGED`, a note is mandatory — ask for it if not provided.
2. Transition status to `APPROVED`.
3. Log to audit_logs: action `APPROVED`, actor `finance_admin`, details include note if provided.
4. Confirm in chat: "Invoice #X (vendor, amount) has been approved. Say 'post invoice #X to QBO' when ready to send to accounting."

## Rejection Flow (Chat)

When operator says `reject invoice #X` with a reason:

1. Transition status to `REJECTED`.
2. Log to audit_logs: action `REJECTED`, actor `finance_admin`, details include reason.
3. Confirm in chat: "Invoice #X has been rejected."
4. If a Slack alert was previously sent for this invoice, send a follow-up Slack message noting the rejection (only if user requests notification).

## QBO Posting Flow (Chat)

When operator says `post invoice #X to QBO` or `post approved invoices to accounting`:

1. Only post invoices with status `APPROVED`.
2. For each invoice, call the Zapier QuickBooks action to create a bill.
3. On success: transition to `POSTED`, log `POSTED` to audit_logs.
4. On failure: transition to `POST_FAILED`, log `POST_FAILED` with error details.
5. Report results to user in a summary table.

## Month-End Report Flow

When prompted `create month-end report`, `share month-end summary`, `post month-end report`, or similar:

1. Call `get_report_summary` for the current month/year and `list_invoices` to gather all data.
2. Build a formatted report covering: summary totals, status breakdown, invoice detail table, flag summary, and key observations.
3. **Slack:** Send the report as a message to the #finance-alerts channel (channel ID from memory or search).
4. **Email:** Send as a real email (NOT a draft) using `gmail_send_email`. The recipient must be the same Gmail address connected for invoice ingestion — identify this by calling `gmail_get_profile` to retrieve the authenticated user's email address. Never leave the `to` field blank for month-end reports.
5. Log to audit_logs with action `MONTH_END_REPORT_SHARED`, including Slack link and email confirmation.
6. Confirm to user that the report was sent to both Slack and email.

**Email template:**

**Subject:** `Invoice Processing Report — <YYYY-MM>`

**Body:**
```
Hi,

Please find below the month-end invoice processing report.

SUMMARY
- Report Date: <today>
- Period: <YYYY-MM>
- Total Invoices Processed: <count>
- Total Payables: $<total>
- Posted to QBO: $<posted_total>
- Pending Review (Flagged): $<flagged_total>
- Approved (not yet posted): $<approved_total>
- Rejected: $<rejected_total>

STATUS BREAKDOWN
- POSTED: <count> invoice(s) — $<amount>
- FLAGGED: <count> invoice(s) — $<amount>
- APPROVED: <count> invoice(s) — $<amount>
- REJECTED: <count> invoice(s) — $<amount>

INVOICE DETAIL
<for each invoice: invoice_number | vendor_name | $total | status | flags>

KEY OBSERVATIONS
<numbered list of notable items>

Regards,
Invoice Processing System
```

## Plain-English Intent Mapping

| What user says | What to do |
|---|---|
| `Start my invoice workspace for today` | init_storage + seed master data if missing, confirm ready |
| `Load my vendor and PO records` | seed/refresh vendor + PO master tables |
| `Get latest invoices from mail` / `Ingest from mail` | Pull Gmail, extract fields from body + attachment metadata, validate, persist |
| `Show invoices waiting for review` | List FLAGGED + READY_FOR_APPROVAL in a table |
| `Approve invoice <id>` | Transition to APPROVED, write audit |
| `Reject invoice <id> with note ...` | Transition to REJECTED, write audit |
| `Post invoice <id> to QBO` / `Post approved invoices` | Post to QBO, mark POSTED or POST_FAILED |
| `Send slack alert of invoice <id>` | Send Slack message with invoice details + approve/reject instructions |
| `Send email alert of invoice <id>` | Send email with invoice details + approve/reject instructions |
| `Share month-end summary` | Compute report, send Slack + email, append sheet audit row |

## Storage Tools

- `init_storage`
- `seed_master_data`
- `upsert_invoice`
- `list_invoices`
- `transition_invoice_status`
- `add_audit_log`
- `get_report_summary`

## References

- `references/workflow.md`
- `references/prompt-pack.md`
- `references/integration-setup.md`
