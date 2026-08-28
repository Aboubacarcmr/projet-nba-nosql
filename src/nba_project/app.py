from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st
from pymongo.errors import PyMongoError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from .aggregations import complete_players, home_win_rate, team_points_by_season, top_scorers
    from .db import get_db
except ImportError:
    from src.nba_project.aggregations import complete_players, home_win_rate, team_points_by_season, top_scorers
    from src.nba_project.db import get_db


st.set_page_config(page_title="NBA NoSQL", layout="wide")


@st.cache_resource
def cached_db():
    return get_db()


def as_dataframe(cursor) -> pd.DataFrame:
    docs = list(cursor)
    for doc in docs:
        doc["_id"] = str(doc.get("_id"))
    return pd.DataFrame(docs)


def collection_counts(db) -> dict[str, int]:
    names = ["games", "teams", "players", "rankings"]
    return {name: db[name].count_documents({}) for name in names}


def render_overview(db) -> None:
    st.subheader("Vue d'ensemble")
    counts = collection_counts(db)
    cols = st.columns(len(counts))
    for col, (name, count) in zip(cols, counts.items()):
        col.metric(name, count)

    st.caption("Derniers matchs importes")
    latest_games = db.games.find(
        {},
        {
            "_id": 1,
            "game_date": 1,
            "season": 1,
            "home_team.name": 1,
            "home_team.points": 1,
            "away_team.name": 1,
            "away_team.points": 1,
            "home_team_wins": 1,
        },
    ).sort("game_date", -1).limit(20)
    st.dataframe(as_dataframe(latest_games), use_container_width=True)


def render_search(db) -> None:
    st.subheader("Recherche")
    mode = st.radio("Type de recherche", ["Par saison", "Par equipe", "Par joueur"], horizontal=True)

    if mode == "Par saison":
        season = st.number_input("Saison", min_value=1940, max_value=2030, value=2021, step=1)
        if st.button("Rechercher les matchs de la saison"):
            cursor = db.games.find(
                {"season": int(season)},
                {"_id": 1, "game_date": 1, "season": 1, "home_team.name": 1, "away_team.name": 1, "home_team_wins": 1},
            ).limit(100)
            st.dataframe(as_dataframe(cursor), use_container_width=True)

    elif mode == "Par equipe":
        team_id = st.number_input("Team ID", min_value=1, value=1610612747, step=1)
        season = st.number_input("Saison", min_value=1940, max_value=2030, value=2021, step=1)
        if st.button("Rechercher les matchs de l'equipe"):
            query = {
                "season": int(season),
                "$or": [
                    {"home_team.team_id": int(team_id)},
                    {"away_team.team_id": int(team_id)},
                ],
            }
            cursor = db.games.find(
                query,
                {"_id": 1, "game_date": 1, "home_team.name": 1, "home_team.points": 1, "away_team.name": 1, "away_team.points": 1},
            ).limit(100)
            st.dataframe(as_dataframe(cursor), use_container_width=True)

    else:
        player_id = st.number_input("Player ID", min_value=1, value=2544, step=1)
        season = st.number_input("Saison", min_value=1940, max_value=2030, value=2021, step=1)
        if st.button("Rechercher les matchs du joueur"):
            cursor = db.games.find(
                {"season": int(season), "player_stats.player_id": int(player_id)},
                {"_id": 1, "game_date": 1, "season": 1, "home_team.name": 1, "away_team.name": 1, "player_stats.$": 1},
            ).limit(100)
            st.dataframe(as_dataframe(cursor), use_container_width=True)


def render_analytics(db) -> None:
    st.subheader("Analyses")
    season = st.number_input("Saison analysee", min_value=1940, max_value=2030, value=2021, step=1)
    analysis = st.selectbox(
        "Aggregation",
        [
            "Top scoreurs",
            "Victoire a domicile",
            "Meilleures attaques equipe/saison",
            "Joueurs les plus complets",
        ],
    )

    if st.button("Lancer l'aggregation"):
        if analysis == "Top scoreurs":
            df = top_scorers(db, int(season))
            st.dataframe(df, use_container_width=True)
            if not df.empty:
                st.bar_chart(df.set_index("player_name")["avg_points"])
        elif analysis == "Victoire a domicile":
            df = home_win_rate(db, int(season))
            st.dataframe(df, use_container_width=True)
            if not df.empty:
                st.bar_chart(df.set_index("team")["win_rate"])
        elif analysis == "Meilleures attaques equipe/saison":
            df = team_points_by_season(db)
            st.dataframe(df, use_container_width=True)
            if not df.empty:
                st.bar_chart(df.set_index("team")["avg_points"])
        else:
            df = complete_players(db, int(season))
            st.dataframe(df, use_container_width=True)
            if not df.empty:
                st.bar_chart(df.set_index("player_name")["complete_score"])


def main() -> None:
    st.title("Analyse NBA - MongoDB Atlas")
    st.write("Interface d'interrogation du projet final NoSQL.")

    try:
        db = cached_db()
    except (RuntimeError, PyMongoError) as exc:
        st.error(f"Connexion impossible : {type(exc).__name__}: {exc}")
        st.info("Verifiez le fichier .env et la variable ATLAS_URI.")
        return

    tabs = st.tabs(["Accueil", "Recherche", "Analyses"])
    with tabs[0]:
        render_overview(db)
    with tabs[1]:
        render_search(db)
    with tabs[2]:
        render_analytics(db)


if __name__ == "__main__":
    main()
