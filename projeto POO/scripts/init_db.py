from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.core.database import SessionLocal, init_db
from backend.app.seed import seed_database


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    print("Banco SQLite inicializado com sucesso.")


if __name__ == "__main__":
    main()

