from pathlib import Path


ROOT = Path(__file__).resolve().parent
REQUIRED = [
    "README.md",
    ".env.example",
    "requirements.txt",
    "src/nba_project/config.py",
    "src/nba_project/db.py",
    "src/nba_project/transform.py",
    "src/nba_project/load_data.py",
    "src/nba_project/crud.py",
    "src/nba_project/indexes.py",
    "src/nba_project/aggregations.py",
    "scripts/backup.ps1",
    "scripts/restore.ps1",
]


def main() -> None:
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    if missing:
        print("Fichiers manquants:")
        for path in missing:
            print(f"- {path}")
        raise SystemExit(1)

    print("Structure projet OK")
    print("Attention: pour charger Atlas, ajoutez les CSV dans data/raw et creez .env depuis .env.example.")


if __name__ == "__main__":
    main()
