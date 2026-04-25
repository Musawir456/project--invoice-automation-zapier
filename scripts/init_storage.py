from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "storage" / "invoice_agent.db"
SCHEMA_PATH = ROOT / "storage" / "schema.sql"
SEED_PATH = ROOT / "seed_data.json"


def init_db(con: sqlite3.Connection) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    con.executescript(schema_sql)
    con.commit()


def seed(con: sqlite3.Connection, data: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()

    # Seed vendors
    vendors_inserted = 0
    for v in data["vendor_master"]:
        existing = con.execute(
            "SELECT id FROM vendors WHERE external_id = ?", (v["id"],)
        ).fetchone()
        if existing:
            continue
        con.execute(
            """INSERT INTO vendors (external_id, name, aliases_json, email, bank_account, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                v["id"],
                v["name"],
                json.dumps(v.get("aliases", [])),
                v.get("email"),
                v.get("bank_account"),
                v.get("status", "active"),
                now,
            ),
        )
        vendors_inserted += 1

    # Seed purchase orders
    pos_inserted = 0
    for po in data["purchase_orders"]:
        existing = con.execute(
            "SELECT id FROM purchase_orders WHERE po_number = ?", (po["po_number"],)
        ).fetchone()
        if existing:
            continue
        con.execute(
            """INSERT INTO purchase_orders (po_number, vendor_external_id, status, total_amount, line_items_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                po["po_number"],
                po["vendor_id"],
                po.get("status", "open"),
                po["total_amount"],
                json.dumps(po.get("line_items", [])),
                now,
            ),
        )
        pos_inserted += 1

    con.commit()
    print(f"Seeded {vendors_inserted} vendor(s), {pos_inserted} purchase order(s).")
    if vendors_inserted == 0 and pos_inserted == 0:
        print("(All records already present — nothing to insert.)")


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    try:
        init_db(con)
        if SEED_PATH.exists():
            seed_data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
            seed(con, seed_data)
    finally:
        con.close()
    print(f"Initialized SQLite storage at: {DB_PATH}")


if __name__ == "__main__":
    main()
