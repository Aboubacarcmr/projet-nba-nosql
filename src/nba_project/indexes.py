from __future__ import annotations

from pprint import pprint

from .db import get_db


INDEXES = [
    ("games", [("season", 1)], "idx_games_season"),
    ("games", [("home_team.team_id", 1), ("season", 1)], "idx_games_home_team_season"),
    ("games", [("away_team.team_id", 1), ("season", 1)], "idx_games_away_team_season"),
    ("games", [("player_stats.player_id", 1), ("season", 1)], "idx_games_player_season"),
    ("rankings", [("team_id", 1), ("season_id", 1), ("standings_date", -1)], "idx_rankings_team_season_date"),
]


QUERIES = [
    ("Matchs d'une saison", "games", {"season": 2021}, None),
    ("Matchs domicile Lakers 2021", "games", {"home_team.team_id": 1610612747, "season": 2021}, None),
    ("Matchs de LeBron James 2021", "games", {"player_stats.player_id": 2544, "season": 2021}, None),
]


def explain_summary(collection, query: dict, sort: dict | None = None) -> dict:
    cursor = collection.find(query)
    if sort:
        cursor = cursor.sort(sort)
    plan = cursor.explain()["executionStats"]
    return {
        "nReturned": plan.get("nReturned"),
        "totalDocsExamined": plan.get("totalDocsExamined"),
        "totalKeysExamined": plan.get("totalKeysExamined"),
        "executionTimeMillis": plan.get("executionTimeMillis"),
    }


def drop_project_indexes(db) -> None:
    for collection_name, _, index_name in INDEXES:
        indexes = db[collection_name].index_information()
        if index_name in indexes:
            db[collection_name].drop_index(index_name)


def create_project_indexes(db) -> None:
    for collection_name, spec, index_name in INDEXES:
        db[collection_name].create_index(spec, name=index_name)
        print(f"INDEX CREE: {collection_name}.{index_name} -> {spec}")


def main() -> None:
    db = get_db()

    print("=== Mesures AVANT index ===")
    drop_project_indexes(db)
    before = {}
    for label, collection_name, query, sort in QUERIES:
        before[label] = explain_summary(db[collection_name], query, sort)
        print(label)
        pprint(before[label])

    print("\n=== Creation des index ===")
    create_project_indexes(db)

    print("\n=== Mesures APRES index ===")
    for label, collection_name, query, sort in QUERIES:
        print(label)
        pprint(explain_summary(db[collection_name], query, sort))


if __name__ == "__main__":
    main()

