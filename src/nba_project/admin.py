from __future__ import annotations

from .db import get_db


def main() -> None:
    db = get_db()
    print("Connexion Atlas OK")
    for name in ["games", "teams", "players", "rankings"]:
        print(f"{name}: {db[name].count_documents({})} documents")


if __name__ == "__main__":
    main()
