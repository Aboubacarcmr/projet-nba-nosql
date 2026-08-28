from __future__ import annotations

from pymongo.errors import DuplicateKeyError, PyMongoError

from .db import get_db


TEST_GAME_ID = "TEST_GAME_NBA_PROJECT"


def create_game(db) -> None:
    doc = {
        "_id": TEST_GAME_ID,
        "game_id": TEST_GAME_ID,
        "game_date": "2026-08-28",
        "season": 2026,
        "status": "Final",
        "home_team_wins": True,
        "home_team": {"team_id": 1, "name": "Demo Home", "points": 101},
        "away_team": {"team_id": 2, "name": "Demo Away", "points": 98},
        "player_stats": [],
    }
    try:
        db.games.insert_one(doc)
        print("CREATE: match de test ajoute")
    except DuplicateKeyError:
        print("CREATE: match de test deja present")


def read_game(db) -> None:
    doc = db.games.find_one({"_id": TEST_GAME_ID}, {"_id": 1, "season": 1, "home_team.points": 1})
    print(f"READ: {doc}")


def update_game(db) -> None:
    result = db.games.update_one({"_id": TEST_GAME_ID}, {"$set": {"home_team.points": 110}})
    print(f"UPDATE: matched={result.matched_count}, modified={result.modified_count}")


def delete_game(db) -> None:
    result = db.games.delete_one({"_id": TEST_GAME_ID})
    print(f"DELETE: deleted={result.deleted_count}")


def main() -> None:
    try:
        db = get_db()
        create_game(db)
        read_game(db)
        update_game(db)
        read_game(db)
        delete_game(db)
    except PyMongoError as exc:
        print(f"ERREUR MongoDB: {type(exc).__name__}: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

