import sqlite3
from pathlib import Path


DB_PATH = Path("cyber_reactor.db")


def main() -> None:
    print(f"DB path: {DB_PATH.resolve()}")
    if not DB_PATH.exists():
        print("DB file not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    tables = [
        row["name"]
        for row in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    ]

    if not tables:
        print("No tables found.")
        conn.close()
        return

    print("\n== TABLES ==")
    for table in tables:
        print(f"- {table}")

    for table in tables:
        print(f"\n== SCHEMA: {table} ==")
        schema = cur.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        print(schema["sql"] if schema and schema["sql"] else "n/a")

        print(f"\n== DATA: {table} ==")
        rows = cur.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            print("(empty)")
            continue

        columns = rows[0].keys()
        print(" | ".join(columns))
        for row in rows:
            print(
                " | ".join(
                    str(row[col]) if row[col] is not None else "NULL"
                    for col in columns
                )
            )

    conn.close()


if __name__ == "__main__":
    main()
