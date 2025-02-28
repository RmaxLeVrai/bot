import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Charger les données du classement une seule fois
excel_file = "nhl_data.xlsx"
standings_df = pd.read_excel(excel_file, sheet_name="Standings")

# Uniformiser le nom de la colonne d'équipe
if "teamCommonName.default" in standings_df.columns:
    standings_df.rename(columns={"teamCommonName.default": "Team"}, inplace=True)
else:
    standings_df.rename(columns={standings_df.columns[0]: "Team"}, inplace=True)

def load_model_and_scaler():
    # Charger les données des matchs
    df_matches = pd.read_excel(excel_file, sheet_name="Match Results")

    # Fusionner les données des matchs avec le classement
    df_merged = df_matches.merge(standings_df, left_on="Home Team", right_on="Team", how="left", suffixes=("", "_home"))
    home_cols = {col: col + "_home" for col in standings_df.columns if col != "Team"}
    df_merged.rename(columns=home_cols, inplace=True)

    df_merged = df_merged.merge(standings_df, left_on="Away Team", right_on="Team", how="left", suffixes=("", "_away"))
    away_cols = {col: col + "_away" for col in standings_df.columns if col != "Team"}
    df_merged.rename(columns=away_cols, inplace=True)

    # Créer la variable cible
    def get_outcome(row):
        if row["Winner"] == row["Home Team"]:
            return "Home"
        elif row["Winner"] == row["Away Team"]:
            return "Away"
        else:
            return "Tie"

    df_merged["Outcome"] = df_merged.apply(get_outcome, axis=1)

    # Sélectionner les features
    features_home = ["wins_home", "losses_home", "points_home", "goalDifferential_home", "winPctg_home", 
                     "homeWins_home", "roadWins_home", "l10Wins_home", "l10Points_home", "streakCount_home"]
    features_away = ["wins_away", "losses_away", "points_away", "goalDifferential_away", "winPctg_away", 
                     "homeWins_away", "roadWins_away", "l10Wins_away", "l10Points_away", "streakCount_away"]

    selected_features = []
    for feat in features_home + features_away:
        if feat in df_merged.columns:
            selected_features.append(feat)

    df_model = df_merged.dropna(subset=selected_features + ["Outcome"]).copy()

    # Préparer les données pour le modèle
    X = df_model[selected_features]
    y = df_model["Outcome"].map({"Home": 0, "Away": 1, "Tie": 2})

    # Division en jeu d'entraînement et de test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Mise à l'échelle des caractéristiques
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Entraînement du modèle
    lr = LogisticRegression(
        solver='lbfgs',
        max_iter=2000,
        random_state=42,
    )
    lr.fit(X_train_scaled, y_train)

    # Prédictions sur le jeu de test
    y_pred = lr.predict(X_test_scaled)
    print("Rapport de classification :")
    print(classification_report(y_test, y_pred, target_names=["Home", "Away", "Tie"], zero_division=0))

    # Sauvegarder le modèle et le scaler
    joblib.dump(lr, "nhl_model.pkl")
    joblib.dump(scaler, "nhl_scaler.pkl")

    return lr, scaler

def predict_match_probability(home_team, away_team, model, scaler):
    # Utiliser le standings_df chargé au début du fichier
    global standings_df

    # Liste des features de base
    base_features = ["wins", "losses", "points", "goalDifferential", "winPctg",
                     "homeWins", "roadWins", "l10Wins", "l10Points", "streakCount"]

    # Sélectionner les données pour chaque équipe
    home_data = standings_df[standings_df["Team"] == home_team]
    away_data = standings_df[standings_df["Team"] == away_team]

    if home_data.empty or away_data.empty:
        raise ValueError("Données manquantes pour l'une des équipes. Vérifiez l'orthographe ou l'uniformité des noms d'équipe.")

    # Extraire les features de base pour chaque équipe
    home_features = home_data.iloc[0][base_features].rename(lambda x: f"{x}_home")
    away_features = away_data.iloc[0][base_features].rename(lambda x: f"{x}_away")

    # Concaténer les deux séries pour constituer le vecteur de features du match
    match_features = pd.concat([home_features, away_features]).to_frame().T

    # Mise à l'échelle des caractéristiques
    match_features_scaled = scaler.transform(match_features)

    # Prédire les probabilités pour chaque classe (Home, Away, Tie)
    prob = model.predict_proba(match_features_scaled)
    return {"Home Win": prob[0][0], "Away Win": prob[0][1], "Tie": prob[0][2]}