# Invoice Agent Desktop — Configuration

This file stores fixed configuration values for the invoice workflow.
Claude must always use these values without asking the user.

## Gmail
| Setting | Value |
|---|---|
| Invoice fetch account | `hezlinaami30@gmail.com` |
| Outbound email recipient | `hezlinaami30@gmail.com` |
| Email tool | Zapier `gmail_send_email` only |

## Slack
| Setting | Value |
|---|---|
| Alerts channel | `#finance-alerts` |
| Channel ID | `C0AM5BJ2X3J` |
| Used for | Invoice alerts, month-end reports, rejection notices |
| Slack tool | Zapier `slack_send_channel_message` only |

## QuickBooks
| Setting | Value |
|---|---|
| QBO tool | Zapier `quickbooks_*` only |

## Rules
- Never ask the user for a Slack channel or email recipient — always use the values above.
- All integrations (Gmail, Slack, QBO) must go through Zapier MCP only.
- SQLite MCP is the only non-Zapier MCP permitted.
