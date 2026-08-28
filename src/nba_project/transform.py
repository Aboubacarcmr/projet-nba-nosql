from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .config import DATA_PROCESSED, required_raw_files


def _clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _to_int(value: Any) -> int | None:
    value = _clean_value(value)
    if value in (None, ""):
        return None
    return int(float(value))


def _to_float(value: Any) -> float | None:
    value = _clean_value(value)
    if value in (None, ""):
        return None
    return float(value)


def _str(value: Any) -> str | None:
    value = _clean_value(value)
    return None if value is None else str(value)


def _first_present(row: dict[str, Any], *columns: str) -> Any:
    for column in columns:
        value = row.get(column)
        if not pd.isna(value):
            return value
    return None


def read_csvs() -> dict[str, pd.DataFrame]:
    files = required_raw_files()
    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Fichiers CSV manquants dans data/raw: " + ", ".join(missing))
    return {name: pd.read_csv(path, low_memory=False) for name, path in files.items()}


def build_teams(df: pd.DataFrame) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for row in df.drop_duplicates("TEAM_ID").to_dict("records"):
        team_id = _to_int(row.get("TEAM_ID"))
        docs.append({
            "_id": team_id,
            "team_id": team_id,
            "abbreviation": _str(row.get("ABBREVIATION")),
            "nickname": _str(row.get("NICKNAME")),
            "city": _str(row.get("CITY")),
            "arena": _str(row.get("ARENA")),
            "year_founded": _to_int(row.get("YEARFOUNDED")),
            "min_year": _to_int(row.get("MIN_YEAR")),
            "max_year": _to_int(row.get("MAX_YEAR")),
        })
    return docs


def build_players(df: pd.DataFrame) -> list[dict[str, Any]]:
    docs_by_id: dict[int, dict[str, Any]] = {}
    for row in df.to_dict("records"):
        player_id = _to_int(row.get("PLAYER_ID"))
        if player_id is None:
            continue
        docs_by_id.setdefault(player_id, {
            "_id": player_id,
            "player_id": player_id,
            "player_name": _str(row.get("PLAYER_NAME")),
            "seasons": [],
            "team_ids": [],
        })
        season = _to_int(row.get("SEASON"))
        team_id = _to_int(row.get("TEAM_ID"))
        if season is not None and season not in docs_by_id[player_id]["seasons"]:
            docs_by_id[player_id]["seasons"].append(season)
        if team_id is not None and team_id not in docs_by_id[player_id]["team_ids"]:
            docs_by_id[player_id]["team_ids"].append(team_id)
    return list(docs_by_id.values())


def build_rankings(df: pd.DataFrame) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for index, row in enumerate(df.to_dict("records")):
        team_id = _to_int(row.get("TEAM_ID"))
        season_id = _to_int(row.get("SEASON_ID"))
        standings_date = _str(row.get("STANDINGSDATE"))
        docs.append({
            "_id": f"{team_id}:{season_id}:{standings_date}:{index}",
            "team_id": team_id,
            "season_id": season_id,
            "standings_date": standings_date,
            "conference": _str(row.get("CONFERENCE")),
            "team": _str(row.get("TEAM")),
            "games": _to_int(row.get("G")),
            "wins": _to_int(row.get("W")),
            "losses": _to_int(row.get("L")),
            "win_pct": _to_float(row.get("W_PCT")),
            "home_record": _str(row.get("HOME_RECORD")),
            "road_record": _str(row.get("ROAD_RECORD")),
        })
    return docs


def _team_name(teams_by_id: dict[int, dict[str, Any]], team_id: int | None) -> str | None:
    if team_id is None:
        return None
    team = teams_by_id.get(team_id)
    if not team:
        return None
    city = team.get("city")
    nickname = team.get("nickname")
    return " ".join(part for part in [city, nickname] if part)


def _player_stat(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "player_id": _to_int(row.get("PLAYER_ID")),
        "player_name": _str(row.get("PLAYER_NAME")),
        "team_id": _to_int(row.get("TEAM_ID")),
        "team_abbreviation": _str(row.get("TEAM_ABBREVIATION")),
        "start_position": _str(row.get("START_POSITION")),
        "minutes": _str(row.get("MIN")),
        "points": _to_float(row.get("PTS")),
        "rebounds": _to_float(row.get("REB")),
        "assists": _to_float(row.get("AST")),
        "steals": _to_float(row.get("STL")),
        "blocks": _to_float(row.get("BLK")),
        "turnovers": _to_float(row.get("TO")),
        "personal_fouls": _to_float(row.get("PF")),
        "plus_minus": _to_float(row.get("PLUS_MINUS")),
    }


def build_games(games: pd.DataFrame, details: pd.DataFrame, teams_docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    teams_by_id = {team["team_id"]: team for team in teams_docs}
    details_by_game: dict[str, list[dict[str, Any]]] = {}
    for row in details.to_dict("records"):
        game_id = _str(row.get("GAME_ID"))
        if not game_id:
            continue
        stat = _player_stat(row)
        if stat["player_id"] is not None:
            details_by_game.setdefault(game_id, []).append(stat)

    docs: list[dict[str, Any]] = []
    for row in games.to_dict("records"):
        game_id = _str(row.get("GAME_ID"))
        home_id = _to_int(_first_present(row, "HOME_TEAM_ID", "TEAM_ID_home"))
        away_id = _to_int(_first_present(row, "VISITOR_TEAM_ID", "TEAM_ID_away"))
        docs.append({
            "_id": game_id,
            "game_id": game_id,
            "game_date": _str(row.get("GAME_DATE_EST")),
            "season": _to_int(row.get("SEASON")),
            "status": _str(row.get("GAME_STATUS_TEXT")),
            "home_team_wins": bool(_to_int(row.get("HOME_TEAM_WINS"))),
            "home_team": {
                "team_id": home_id,
                "name": _team_name(teams_by_id, home_id),
                "points": _to_float(row.get("PTS_home")),
                "field_goal_pct": _to_float(row.get("FG_PCT_home")),
                "free_throw_pct": _to_float(row.get("FT_PCT_home")),
                "three_point_pct": _to_float(row.get("FG3_PCT_home")),
                "assists": _to_float(row.get("AST_home")),
                "rebounds": _to_float(row.get("REB_home")),
            },
            "away_team": {
                "team_id": away_id,
                "name": _team_name(teams_by_id, away_id),
                "points": _to_float(row.get("PTS_away")),
                "field_goal_pct": _to_float(row.get("FG_PCT_away")),
                "free_throw_pct": _to_float(row.get("FT_PCT_away")),
                "three_point_pct": _to_float(row.get("FG3_PCT_away")),
                "assists": _to_float(row.get("AST_away")),
                "rebounds": _to_float(row.get("REB_away")),
            },
            "player_stats": details_by_game.get(game_id, []),
        })
    return docs


def build_documents() -> dict[str, list[dict[str, Any]]]:
    csvs = read_csvs()
    teams = build_teams(csvs["teams"])
    return {
        "teams": teams,
        "players": build_players(csvs["players"]),
        "rankings": build_rankings(csvs["ranking"]),
        "games": build_games(csvs["games"], csvs["games_details"], teams),
    }


def export_processed_json() -> None:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    for collection, docs in build_documents().items():
        pd.Series(docs).to_json(DATA_PROCESSED / f"{collection}.json", orient="values", force_ascii=False)
