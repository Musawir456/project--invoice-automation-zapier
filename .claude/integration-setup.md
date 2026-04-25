# Integration Setup (Claude Desktop Only)

## A) Open Project

1. Open Claude Desktop -> Code.
2. Select folder `PROJECT_2_CLAUDECODE_ZAPIERMCP`.
3. Restart Claude Desktop once after opening folder so `.mcp.json` is loaded.

## B) Enable SQLite MCP Persistence

1. Install dependency:
   - `pip install mcp`
2. Initialize DB:
   - `python scripts/init_storage.py`
3. Ensure `.mcp.json` points to:
   - `python mcp/sqlite_store_server.py`
4. Restart Claude Desktop.
5. In chat, invoke storage flow using skill instructions.

## C) Load Skill

Skill path:

- `.claude/skills/invoice-agent-desktop/skill.md`

Use it in prompt:

- `Use invoice-agent-desktop skill and start the workflow.`

## D) Connect External Apps in Claude Desktop

Connect Zapier MCP in Claude Desktop connector settings, then use Zapier-managed actions for:

1. Gmail
2. Slack
3. QuickBooks
4. Google Sheets

Authorize Zapier once, and confirm these actions are available through Zapier MCP tools.

## E) First Run

1. `Use invoice-agent-desktop skill.`
2. `Initialize storage and seed master data.`
3. `Get latest invoice emails and persist extracted invoices.`
4. `Show invoice table with id, vendor, total, status, flags.`
5. `Approve or reject selected invoices and write audit logs.`
6. `Post approved invoices to QBO.`
7. `Share report to Slack and email; append sheet audit rows.`
