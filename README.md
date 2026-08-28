# Projet final NoSQL - Analyse des performances NBA

## Sujet

**Analyse des performances sportives NBA : matchs, equipes, joueurs et saisons**

Jeu de donnees : **NBA Games Dataset**  
Lien : https://www.kaggle.com/datasets/nathanlauga/nba-games

Le projet construit une base MongoDB Atlas a partir de donnees NBA reelles. L'objectif est d'analyser les performances des equipes et des joueurs par match et par saison.

---

## Reponse au cahier des charges

| Exigence | Reponse du projet |
|---|---|
| Base deployee sur Atlas | Les scripts se connectent a Atlas via `ATLAS_URI` dans `.env` |
| Jeu de donnees reel | Dataset Kaggle `nathanlauga/nba-games` |
| Au moins 10 000 documents | Le dataset contient des milliers de matchs, details de matchs, joueurs et lignes de classement |
| Donnees imbriquees/tableaux | Les statistiques joueurs sont embarquees dans `games.player_stats[]` |
| Au moins deux entites reliees | Matchs, equipes, joueurs et classements sont relies par identifiants |
| Dimension temporelle | Dates de matchs, saisons, historique des classements |
| CRUD Python | `src/nba_project/crud.py` |
| Index mesures avec `explain` | `src/nba_project/indexes.py` |
| Aggregations et visualisations | `src/nba_project/aggregations.py` genere tables Markdown et graphiques |
| Sauvegarde/restauration | `scripts/backup.ps1` et `scripts/restore.ps1` |
| Depot propre | `.env` et donnees lourdes ignorees par `.gitignore` |
| Interface d'interrogation | Interface Streamlit dans `src/nba_project/app.py` |
| Code structure | Modules Python reutilisables dans `src/nba_project/` |

---

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copier ensuite `.env.example` vers `.env` :

```powershell
Copy-Item .env.example .env
```

Puis renseigner :

```text
ATLAS_URI=mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME=nba
```

Le fichier `.env` ne doit jamais etre depose dans GitHub ou Teams.

---

## Chargement des donnees

Telecharger le dataset Kaggle puis placer les cinq CSV ici :

```text
data/raw/games.csv
data/raw/games_details.csv
data/raw/players.csv
data/raw/ranking.csv
data/raw/teams.csv
```

Commande de chargement sur Atlas :

```powershell
python -m src.nba_project.load_data
```

Collections creees :

| Collection | Source | Role |
|---|---|---|
| `games` | `games.csv` + `games_details.csv` + `teams.csv` | Matchs enrichis avec equipes et statistiques joueurs |
| `teams` | `teams.csv` | Informations fixes des equipes |
| `players` | `players.csv` | Informations fixes des joueurs |
| `rankings` | `ranking.csv` | Classements historiques par equipe/date/saison |

Verification rapide :

```powershell
python -m src.nba_project.admin
```

---

## Pourquoi MongoDB plutot que PostgreSQL ?

MongoDB est choisi parce que le match NBA est un objet metier naturellement documentaire. Un match contient une date, une saison, deux equipes, des scores et une liste de statistiques individuelles.

Dans PostgreSQL, le modele d'origine resterait tres relationnel avec plusieurs tables et des jointures frequentes entre `games`, `games_details`, `players` et `teams`. Ici, notre requete principale est la consultation et l'analyse d'un match complet. MongoDB permet donc de rapprocher les donnees lues ensemble.

Le choix n'est pas gratuit : il ajoute de la duplication, notamment le nom des joueurs et quelques informations d'equipe dans les matchs. Ce cout est accepte car il simplifie les lectures principales et les aggregations par match/saison.

---

## Schema documentaire

```text
games
  - _id / game_id
  - game_date
  - season
  - status
  - home_team_wins
  - home_team
      - team_id
      - name
      - points
      - field_goal_pct
      - free_throw_pct
      - three_point_pct
      - assists
      - rebounds
  - away_team
      - team_id
      - name
      - points
      - field_goal_pct
      - free_throw_pct
      - three_point_pct
      - assists
      - rebounds
  - player_stats[]
      - player_id
      - player_name
      - team_id
      - team_abbreviation
      - minutes
      - points
      - rebounds
      - assists
      - steals
      - blocks
      - turnovers
      - plus_minus

teams
  - _id / team_id
  - abbreviation
  - nickname
  - city
  - arena
  - year_founded

players
  - _id / player_id
  - player_name
  - seasons[]
  - team_ids[]

rankings
  - team_id
  - season_id
  - standings_date
  - conference
  - wins
  - losses
  - win_pct
```

---

## Fiche de modelisation

| Relation | Cardinalite | Decision | Question qui a tranche | Ce que ca coute |
|---|---:|---|---|---|
| Match -> statistiques joueurs | 1 -> N | Embarquer `player_stats[]` dans `games` | Consulte-t-on souvent un match avec ses joueurs ? Oui | Documents `games` plus gros, index multikey necessaire |
| Match -> equipe domicile/exterieur | N -> 1 | Denormaliser un resume d'equipe dans `games`, garder `teams` separe | A-t-on besoin du nom de l'equipe dans chaque match ? Oui | Duplication partielle des noms/equipes |
| Joueur -> performances de match | 1 -> N | Garder `players` separe, referencer par `player_id` dans `player_stats` | Les joueurs apparaissent dans beaucoup de matchs | Pour l'historique complet d'un joueur, il faut parcourir `games.player_stats[]` |
| Equipe -> classements | 1 -> N | Garder `rankings` separe | Le classement evolue dans le temps | Analyses croisees avec matchs via requetes supplementaires ou `$lookup` |

---

## CRUD Python

Script :

```powershell
python -m src.nba_project.crud
```

Operations couvertes :

| Operation | Exemple |
|---|---|
| Create | Ajouter un match de test |
| Read | Lire ce match |
| Update | Modifier son score |
| Delete | Supprimer le match de test |

Les erreurs de connexion et les doublons sont gerees dans le code.

---

## Index et mesures `explain`

Script :

```powershell
python -m src.nba_project.indexes
```

Index prevus :

| Index | Requete servie | Justification |
|---|---|---|
| `{ season: 1 }` sur `games` | Matchs d'une saison | Beaucoup d'analyses sont filtrees par saison |
| `{ "home_team.team_id": 1, season: 1 }` sur `games` | Matchs domicile d'une equipe | Sert l'analyse de l'avantage du terrain |
| `{ "away_team.team_id": 1, season: 1 }` sur `games` | Matchs exterieur d'une equipe | Complete les analyses equipe/saison |
| `{ "player_stats.player_id": 1, season: 1 }` sur `games` | Matchs d'un joueur | Index multikey pour les tableaux de statistiques joueurs |
| `{ team_id: 1, season_id: 1, standings_date: -1 }` sur `rankings` | Classement d'une equipe dans le temps | Sert l'analyse temporelle des rankings |

Le script affiche pour chaque requete :

- `nReturned` ;
- `totalDocsExamined` ;
- `totalKeysExamined` ;
- `executionTimeMillis`.

La comparaison avant/apres montre l'effet des index.

---

## Aggregations et visualisations

Script :

```powershell
python -m src.nba_project.aggregations
```

Aggregations prevues :

| Aggregation | Question metier |
|---|---|
| Top 10 des joueurs par moyenne de points | Quels joueurs marquent le plus sur une saison ? |
| Taux de victoire a domicile par equipe | Quelles equipes profitent le plus du terrain ? |
| Moyenne de points equipe/saison | Quelles equipes ont les meilleures attaques ? |
| Joueurs les plus complets | Qui combine points, rebonds et passes ? |

Sorties generees :

```text
outputs/rapport_analytique.md
outputs/top_scorers.png
outputs/home_win_rate.png
```

---

## Interface d'interrogation

L'interface permet d'utiliser le projet sans taper de requetes MongoDB dans un terminal.

Lancement :

```powershell
streamlit run src/nba_project/app.py
```

Fonctionnalites :

| Onglet | Utilite |
|---|---|
| Accueil | Verifier la connexion Atlas, afficher le volume des collections et les derniers matchs |
| Recherche | Rechercher des matchs par saison, par equipe ou par joueur |
| Analyses | Lancer des aggregations et afficher les resultats sous forme de tableaux et graphiques |

Cette interface interroge directement les collections MongoDB Atlas via la meme configuration `.env` que les scripts Python.

---

## Sauvegarde et restauration

Sauvegarde :

```powershell
.\scripts\backup.ps1
```

Restauration :

```powershell
.\scripts\restore.ps1 -BackupPath .\backups\YYYYMMDD_HHMMSS
```

La restauration utilise `--drop` pour remettre la base dans l'etat exact de la sauvegarde.

---

## Organisation du code

Le projet est organise en modules Python reutilisables. L'objectif est d'eviter un notebook unique difficile a relancer et de separer clairement les responsabilites du projet.

Structure principale :

```text
src/nba_project/
  config.py          # lecture de .env, chemins du projet, fichiers attendus
  db.py              # connexion MongoDB Atlas
  transform.py       # lecture CSV et transformation en documents MongoDB
  load_data.py       # chargement des collections dans Atlas
  crud.py            # operations Create, Read, Update, Delete
  indexes.py         # creation des index et mesures explain avant/apres
  aggregations.py    # pipelines d'aggregation et generation des graphiques
  app.py             # interface Streamlit
  admin.py           # verification rapide des volumes en base
```

Cette organisation permet de lancer chaque partie separement :

```powershell
python -m src.nba_project.load_data
python -m src.nba_project.admin
python -m src.nba_project.crud
python -m src.nba_project.indexes
python -m src.nba_project.aggregations
streamlit run src/nba_project/app.py
```

Chaque fichier a un role precis. La transformation des CSV est isolee dans `transform.py`, la connexion Atlas est centralisee dans `db.py`, et les traitements metier sont separes entre CRUD, index, aggregations et interface. Cela rend le projet plus simple a relire, a corriger et a presenter pendant la soutenance.
