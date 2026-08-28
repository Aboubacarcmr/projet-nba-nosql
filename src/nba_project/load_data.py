from __future__ import annotations

from pymongo.errors import PyMongoError

from .db import get_db
from .transform import build_documents


def load_collection(db, name: str, docs: list[dict]) -> None:
    collection = db[name]
    collection.drop()
    if docs:
        collection.insert_many(docs, ordered=False)
    print(f"{name}: {collection.count_documents({})} documents charges")


def main() -> None:
    try:
        db = get_db()
        for name, docs in build_documents().items():
            load_collection(db, name, docs)
        print("Chargement termine sur Atlas.")
    except (FileNotFoundError, RuntimeError, PyMongoError) as exc:
        print(f"ERREUR: {type(exc).__name__}: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

