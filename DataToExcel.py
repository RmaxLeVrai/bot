import requests
import pandas as pd
from datetime import datetime, timedelta
import os

# Définition du chemin du fichier
file_path = "nhl_data.xlsx"

# Vérifier si le fichier existe, sinon le créer
if not os.path.exists(file_path):
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        # Création de feuilles vides
        pd.DataFrame(columns=["Date", "Home Team", "Away Team", "Winner"]).to_excel(writer, sheet_name="Match Results", index=False)
        pd.DataFrame(columns=["Team", "wins", "losses", "points"]).to_excel(writer, sheet_name="Standings", index=False)
    print(f"✅ Fichier '{file_path}' créé avec des feuilles vides.")

# Charger le fichier Excel (il existe maintenant à coup sûr)
df_matches = pd.read_excel(file_path, sheet_name="Match Results")
df_standings = pd.read_excel(file_path, sheet_name="Standings")

# ----------------- PARTIE 1 : RÉCUPÉRATION DES CLASSEMENTS -----------------

def fetch_nhl_standings():
    url = "https://api-web.nhle.com/v1/standings/now"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Erreur lors de l'appel API, status code: {response.status_code}")
    return response.json()

def flatten_standings(api_data):
    df = pd.json_normalize(api_data.get("standings", []))
    return df

def filter_standings(df):
    columns_to_keep = [
        "teamCommonName.default",
        "gamesPlayed", "wins", "losses", "otLosses", "ties",
        "winPctg", "points", "goalFor", "goalAgainst", "goalDifferential",
        "homeWins", "homeLosses", "roadWins", "roadLosses", 
        "l10Wins", "l10Losses", "l10Points", "streakCode", "streakCount"
    ]
    available_cols = [col for col in columns_to_keep if col in df.columns]
    return df[available_cols]

# ----------------- PARTIE 2 : RÉCUPÉRATION DES RÉSULTATS DE MATCHS -----------------

def get_scores_for_date(date):
    url = f"https://api-web.nhle.com/v1/score/{date}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur lors de la récupération des données pour {date}")
        return None

def extract_match_data(data):
    matches = []
    try:
        for game in data.get('games', []):
            home_team = game['homeTeam']['name']['default']
            away_team = game['awayTeam']['name']['default']
            home_score = game['homeTeam']['score']
            away_score = game['awayTeam']['score']
            is_overtime = game.get('gameOutcome', {}).get('lastPeriodType') == "OT"
            winner = "Tie" if is_overtime else (home_team if home_score > away_score else away_team)

            matches.append({
                'Date': game['gameDate'][:10], 'Home Team': home_team, 'Away Team': away_team,
                'Home Score': home_score, 'Away Score': away_score,
                'Winner': winner, 'Overtime': is_overtime
            })
        return matches
    except Exception as e:
        print(f"Erreur lors de l'extraction des données : {e}")
        return matches

def get_last_date_from_excel(file_path, sheet_name):
    if os.path.exists(file_path):
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        if not df.empty:
            last_date = df['Date'].max()
            return datetime.strptime(last_date, "%Y-%m-%d")
    return None

def update_nhl_scores(file_path):
    last_date = get_last_date_from_excel(file_path, "Match Results")
    if last_date is None:
        last_date = datetime.strptime("2024-10-04", "%Y-%m-%d")
    else:
        last_date += timedelta(days=1)
    
    end_date = datetime.now()
    all_matches = []

    while last_date <= end_date:
        date_str = last_date.strftime("%Y-%m-%d")
        print(f"Récupération des données pour {date_str}...")
        data = get_scores_for_date(date_str)
        
        if data:
            matches = extract_match_data(data)
            all_matches.extend(matches)
        
        last_date += timedelta(days=1)

    if all_matches:
        new_df = pd.DataFrame(all_matches)
        with pd.ExcelWriter(file_path, mode="a", if_sheet_exists="replace") as writer:
            new_df.to_excel(writer, sheet_name="Match Results", index=False)
        print(f"Fichier Excel mis à jour avec {len(all_matches)} nouveaux matchs.")
    else:
        print("Aucun nouveau match trouvé.")

# ----------------- PARTIE 3 : SAUVEGARDE DANS UN FICHIER EXCEL UNIQUE -----------------

def save_to_excel(file_path):
    # Récupération et mise en forme des classements
    data = fetch_nhl_standings()
    df_standings = flatten_standings(data)
    df_standings = filter_standings(df_standings)

    # Sauvegarde des classements dans le fichier Excel
    with pd.ExcelWriter(file_path, mode="a", if_sheet_exists="replace") as writer:
        df_standings.to_excel(writer, sheet_name="Standings", index=False)
    
    print(f"Les classements ont été mis à jour dans '{file_path}'.")


file_path = "nhl_data.xlsx"
update_nhl_scores(file_path)  # Mettre à jour les résultats des matchs
save_to_excel(file_path)      # Mettre à jour les classements
