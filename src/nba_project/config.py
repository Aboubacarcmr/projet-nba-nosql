from pathlib import Path
import os

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
OUTPUTS = ROOT_DIR / "outputs"


def load_settings() -> tuple[str, str]:
    load_dotenv(ROOT_DIR / ".env", override=True)
    uri = os.environ.get("ATLAS_URI")
    db_name = os.environ.get("DB_NAME", "nba")
    if not uri:
        raise RuntimeError("ATLAS_URI est absent. Copiez .env.example en .env puis renseignez l'URI Atlas.")
    return uri, db_name


def required_raw_files() -> dict[str, Path]:
    return {
        "games": DATA_RAW / "games.csv",
        "games_details": DATA_RAW / "games_details.csv",
        "players": DATA_RAW / "players.csv",
        "ranking": DATA_RAW / "ranking.csv",
        "teams": DATA_RAW / "teams.csv",
    }

