from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .config import OUTPUTS
from .db import get_db


def save_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    filename: str
) -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    ax = df.plot(
        kind="bar",
        x=x,
        y=y,
        legend=False,
        figsize=(10, 5)
    )

    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel(y)

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    plt.savefig(OUTPUTS / filename)
    plt.close()


def top_scorers(db, season: int = 2021) -> pd.DataFrame:
    pipeline = [
        {"$match": {"season": season}},

        {"$unwind": "$player_stats"},

        {
            "$match": {
                "player_stats.points": {"$ne": None}
            }
        },

        {
            "$group": {
                "_id": {
                    "player_id": "$player_stats.player_id",
                    "player_name": "$player_stats.player_name",
                },
                "games": {"$sum": 1},
                "avg_points": {"$avg": "$player_stats.points"},
            }
        },

        {
            "$match": {
                "games": {"$gte": 10}
            }
        },

        {
            "$sort": {
                "avg_points": -1
            }
        },

        {"$limit": 10},

        {
            "$project": {
                "_id": 0,
                "player_name": "$_id.player_name",
                "games": 1,
                "avg_points": {
                    "$round": ["$avg_points", 2]
                },
            }
        },
    ]

    return pd.DataFrame(
        list(db.games.aggregate(pipeline))
    )


def home_win_rate(db, season: int = 2021) -> pd.DataFrame:
    pipeline = [
        {
            "$match": {
                "season": season
            }
        },

        {
            "$group": {
                "_id": "$home_team.name",
                "home_games": {"$sum": 1},
                "home_wins": {
                    "$sum": {
                        "$cond": [
                            "$home_team_wins",
                            1,
                            0
                        ]
                    }
                },
            }
        },

        {
            "$project": {
                "_id": 0,
                "team": "$_id",
                "home_games": 1,
                "home_wins": 1,
                "win_rate": {
                    "$round": [
                        {
                            "$multiply": [
                                {
                                    "$divide": [
                                        "$home_wins",
                                        "$home_games"
                                    ]
                                },
                                100
                            ]
                        },
                        2
                    ]
                },
            }
        },

        {
            "$sort": {
                "win_rate": -1
            }
        },

        {"$limit": 10},
    ]

    return pd.DataFrame(
        list(db.games.aggregate(pipeline))
    )


def team_points_by_season(db) -> pd.DataFrame:
    pipeline = [
        {
            "$project": {
                "season": 1,
                "teams": [
                    {
                        "name": "$home_team.name",
                        "points": "$home_team.points"
                    },
                    {
                        "name": "$away_team.name",
                        "points": "$away_team.points"
                    },
                ],
            }
        },

        {"$unwind": "$teams"},

        {
            "$match": {
                "teams.points": {"$ne": None}
            }
        },

        {
            "$group": {
                "_id": {
                    "season": "$season",
                    "team": "$teams.name"
                },
                "avg_points": {
                    "$avg": "$teams.points"
                },
                "games": {
                    "$sum": 1
                },
            }
        },

        {
            "$match": {
                "games": {"$gte": 20}
            }
        },

        {
            "$sort": {
                "avg_points": -1
            }
        },

        {"$limit": 10},

        {
            "$project": {
                "_id": 0,
                "season": "$_id.season",
                "team": "$_id.team",
                "games": 1,
                "avg_points": {
                    "$round": [
                        "$avg_points",
                        2
                    ]
                },
            }
        },
    ]

    return pd.DataFrame(
        list(db.games.aggregate(pipeline))
    )


def complete_players(db, season: int = 2021) -> pd.DataFrame:
    pipeline = [
        {
            "$match": {
                "season": season
            }
        },

        {
            "$unwind": "$player_stats"
        },

        {
            "$match": {
                "player_stats.points": {"$ne": None},
                "player_stats.rebounds": {"$ne": None},
                "player_stats.assists": {"$ne": None},
            }
        },

        {
            "$group": {
                "_id": "$player_stats.player_name",
                "games": {"$sum": 1},
                "avg_points": {
                    "$avg": "$player_stats.points"
                },
                "avg_rebounds": {
                    "$avg": "$player_stats.rebounds"
                },
                "avg_assists": {
                    "$avg": "$player_stats.assists"
                },
            }
        },

        {
            "$match": {
                "games": {"$gte": 10}
            }
        },

        {
            "$addFields": {
                "complete_score": {
                    "$add": [
                        "$avg_points",
                        "$avg_rebounds",
                        "$avg_assists"
                    ]
                }
            }
        },

        {
            "$sort": {
                "complete_score": -1
            }
        },

        {"$limit": 10},

        {
            "$project": {
                "_id": 0,
                "player_name": "$_id",
                "games": 1,

                "avg_points": {
                    "$round": [
                        "$avg_points",
                        2
                    ]
                },

                "avg_rebounds": {
                    "$round": [
                        "$avg_rebounds",
                        2
                    ]
                },

                "avg_assists": {
                    "$round": [
                        "$avg_assists",
                        2
                    ]
                },

                "complete_score": {
                    "$round": [
                        "$complete_score",
                        2
                    ]
                },
            }
        },
    ]

    return pd.DataFrame(
        list(db.games.aggregate(pipeline))
    )


def write_report(
    tables: dict[str, pd.DataFrame]
) -> Path:

    OUTPUTS.mkdir(
        parents=True,
        exist_ok=True
    )

    report = OUTPUTS / "rapport_analytique.md"

    lines = [
        "# Rapport analytique NBA",
        "",
        "Ce rapport est genere depuis MongoDB Atlas par `python -m src.nba_project.aggregations`.",
        "",
    ]

    for title, df in tables.items():

        lines.append(
            f"## {title}"
        )

        lines.append("")

        lines.append(
            df.to_markdown(index=False)
            if not df.empty
            else "Aucun resultat."
        )

        lines.append("")

    report.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    return report


def main() -> None:

    db = get_db()

    tables = {
        "Top 10 des joueurs par moyenne de points":
            top_scorers(db),

        "Top 10 des equipes par taux de victoire a domicile":
            home_win_rate(db),

        "Meilleures moyennes de points equipe/saison":
            team_points_by_season(db),

        "Joueurs les plus complets":
            complete_players(db),
    }

    for title, df in tables.items():

        print(
            f"\n=== {title} ==="
        )

        print(
            df.to_string(index=False)
        )

    # Graphique 1 :
    # Top 10 des scoreurs

    if not tables[
        "Top 10 des joueurs par moyenne de points"
    ].empty:

        save_bar_chart(
            tables[
                "Top 10 des joueurs par moyenne de points"
            ],
            "player_name",
            "avg_points",
            "Top scoreurs - saison 2021",
            "top_scorers.png"
        )

    # Graphique 2 :
    # Taux de victoire à domicile

    if not tables[
        "Top 10 des equipes par taux de victoire a domicile"
    ].empty:

        save_bar_chart(
            tables[
                "Top 10 des equipes par taux de victoire a domicile"
            ],
            "team",
            "win_rate",
            "Taux de victoire a domicile - saison 2021",
            "home_win_rate.png"
        )

    # Graphique 3 :
    # Joueurs les plus complets

    if not tables[
        "Joueurs les plus complets"
    ].empty:

        save_bar_chart(
            tables[
                "Joueurs les plus complets"
            ],
            "player_name",
            "complete_score",
            "Joueurs les plus complets - saison 2021",
            "complete_players.png"
        )

    path = write_report(
        tables
    )

    print(
        f"\nRapport genere: {path}"
    )

    print(
        "\nGraphiques generes :"
    )

    print(
        "- outputs/top_scorers.png"
    )

    print(
        "- outputs/home_win_rate.png"
    )

    print(
        "- outputs/complete_players.png"
    )


if __name__ == "__main__":
    main()
