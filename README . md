# Invoice Processing AI Agent using Claude Code 

This project has **no backend service**.  
Everything runs from Claude Desktop Code mode using:

- skills for operational rules/workflow
- a local SQLite MCP server for persistence
- Zapier MCP connector (with QBO, Slack, Gmail, and Google Sheets actions configured in Zapier)

## Architecture

1. Claude Desktop is the UI/orchestrator.
2. Skills define all business rules and required behavior.
3. SQLite MCP server stores invoices, vendor master, PO register, and audit logs.
4. External actions (QBO/Slack/Gmail/Sheets) run through Zapier MCP tools.

## Folder Map

- `.claude/skills/invoice-agent-desktop/skill.md` - core rules/workflow
- `mcp/sqlite_store_server.py` - local SQLite MCP server
- `storage/schema.sql` - DB schema
- `scripts/init_storage.py` - initialize/reset local DB
- `.mcp.json` - MCP server registration
- `seed_data.json` - vendor/PO seed source

## One-Time Setup

### 1) Make sure you have Python 3.11 or higher installed on your computer.

### 2) Python deps for MCP server

```powershell
pip install mcp pdfplumber pypdf
```

### 3) Initialize local SQLite storage

```powershell
python scripts/init_storage.py
```

This creates:

- `storage/invoice_agent.db`

### 4) Load MCP server in Claude Desktop

`.mcp.json` is already included.  
Restart Claude Desktop after opening this folder so MCP tools load (`sqlite_store`).

## Desktop-Only Execution Flow

1. Open Claude Desktop -> **Code**.
2. Select folder: `project-invoice-automation-zapier`.
3. Use skill instructions from `invoice-agent-desktop`.
4. Run workflow conversationally:
   - pull/process invoice emails
   - validate against vendor/PO rules
   - classify `READY_FOR_APPROVAL` or `FLAGGED`
   - approve/reject (single super-user)
   - post approved invoices to QBO
   - write audit rows
   - generate/share reports

## End-User Prompt Examples (Non-Technical)

- `Load my vendor and PO records.`
- `Get latest invoices from mail.`
- `Show invoices waiting for review in a table.`
- `Approve invoice 2 with note Verified.`
- `Reject invoice 3 with note Duplicate.`
- `Post approved invoices to accounting.`
- `Generate month-end summary for 2026-04.`
- `Share month-end summary to Slack and email.`

## Connector Integrations (Desktop side)

Use Claude Desktop connector:

- Zapier MCP (with Gmail, Slack, QuickBooks, and Google Sheets actions configured in Zapier)

QuickBooks posting, Slack notifications, Gmail actions, and Sheets updates are executed via Zapier MCP tools.
No separate backend service is required.

Detailed setup guide:

- `.claude/skills/invoice-agent-desktop/references/integration-setup.md`

## Single User Policy

- One operator only: `finance_admin`
- Full rights for all steps (ingest, approval, posting, reporting)
- Authorization and guardrails are defined in the skill and enforced in workflow prompts
