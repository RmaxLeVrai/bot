import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from prediction import load_model_and_scaler, predict_match_probability
import joblib  # Pour charger le modèle et le scaler
import json
import re

TOKEN = "TOKEN"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

EST = ['Blue Jackets', 'Bruins', 'Canadiens', 'Capitals', 'Devils', 'Flyers', 'Hurricanes',
       'Islanders', 'Lightning', 'Maple Leafs', 'Panthers', 'Penguins', 'Rangers',
       'Red Wings', 'Sabres', 'Senators']
OUEST = ['Avalanche', 'Blackhawks', 'Blues', 'Canucks', 'Coyotes', 'Ducks', 'Flames',
         'Golden Knights', 'Jets', 'Kings', 'Kraken', 'Oilers', 'Predators', 'Sharks', 'Stars', 'Wild']
ALL_TEAMS = EST + OUEST

# Lire le fichier JSON
with open("matches_updated.json", "r", encoding="utf-8") as json_file:
    matches = json.load(json_file)

# Créer une liste de chaînes au format "Équipe1 vs Équipe2"
match_list = []
for match in matches:
    equipe1 = match["equipe1"]["nom"]
    equipe2 = match["equipe2"]["nom"]
    match_list.append(f"{equipe1} vs {equipe2}")
MATCH_TODAY = match_list

async def team_autocomplete(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=team, value=team) for team in ALL_TEAMS if current.lower() in team.lower()][:25]
async def match_today_autocomplete(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=match, value=match) for match in MATCH_TODAY if current.lower() in match.lower()][:25]

@bot.event
async def on_ready():
    print(f'✅ Connecté en tant que {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'✅ {len(synced)} commandes slash synchronisées.')
    except Exception as e:
        print(f'❌ Erreur de synchronisation : {e}')

@bot.tree.command(name="comparer", description="Comparer deux équipes de la NHL")
@app_commands.describe(equipe1="Equipe à domicile", equipe2="Equipe à l'extérieur")
@app_commands.autocomplete(equipe1=team_autocomplete)
@app_commands.autocomplete(equipe2=team_autocomplete)
async def comparer(interaction: discord.Interaction, equipe1: str, equipe2: str):
    if equipe1 not in ALL_TEAMS or equipe2 not in ALL_TEAMS:
        return await interaction.response.send_message("❌ Équipe(s) invalide(s) !", ephemeral=True)

    if equipe1 == equipe2:
        return await interaction.response.send_message("❌ Choisissez deux équipes différentes !", ephemeral=True)

    try:
        # Charger le modèle et le scaler
        model = joblib.load("nhl_model.pkl")
        scaler = joblib.load("nhl_scaler.pkl")

        # Prédiction des probabilités
        result = predict_match_probability(equipe1, equipe2, model, scaler)

        # Création de l'embed
        embed = discord.Embed(
            title="🎯 Prédiction du match",
            color=0x3498db
        )
        embed.add_field(name="Match", value=f"{equipe1} vs {equipe2}", inline=False)

        proba_home = result.get("Home Win", 0)
        proba_away = result.get("Away Win", 0)
        proba_tie  = result.get("Tie", 0)

        embed.add_field(
            name="Probabilité de victoire",
            value=f"🏠 **{equipe1} (Domicile)**: {proba_home*100:.1f}%\n"
                f"✈️ **{equipe2} (Extérieur)**: {proba_away*100:.1f}%\n"
                f"⚖️ **Match nul**: {proba_tie*100:.1f}%",
            inline=False
        )

        best_outcome = max(result, key=result.get)
        if best_outcome == "Home Win":
            recommendation = f"🎲 Parier sur **{equipe1}**"
        elif best_outcome == "Away Win":
            recommendation = f"🎲 Parier sur **{equipe2}**"
        else:
            recommendation = "🎲 Parier sur un **match nul**"

        embed.add_field(name="💡 Recommandation", value=recommendation, inline=False)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        print(f"Erreur de prédiction : {e}")
        await interaction.response.send_message("❌ Erreur lors de la prédiction !", ephemeral=True)

@bot.tree.command(name="matchs_today", description="Voir si le match du jour est une bonne idée pour gagner des sous")
@app_commands.describe(match="séléctionner le match du jour")
@app_commands.autocomplete(match=match_today_autocomplete)
async def match_today(interaction: discord.Interaction, match: str):
    if match not in MATCH_TODAY:
        return await interaction.response.send_message("❌ Le match n'existe pas encore !", ephemeral=True)
    
    try:
        # Extraire les noms des équipes du match sélectionné
        parts = re.split(r"\s+vs\s+", match, flags=re.IGNORECASE)
        if len(parts) != 2:
            raise ValueError("Format invalide")
        equipe1_name, equipe2_name = parts[0].strip(), parts[1].strip()
        
        # Trouver le match correspondant dans les données JSON
        selected_match = None
        for m in matches:
            json_equipe1 = m["equipe1"]["nom"].strip().lower()
            json_equipe2 = m["equipe2"]["nom"].strip().lower()
            if (json_equipe1 == equipe1_name.lower() 
                and json_equipe2 == equipe2_name.lower()):
                selected_match = m
                break
        
        if not selected_match:
            return await interaction.response.send_message("❌ Données du match introuvables !", ephemeral=True)
        
        # Charger le modèle et le scaler
        model = joblib.load("nhl_model.pkl")
        scaler = joblib.load("nhl_scaler.pkl")
        
        # Extraire les cotes
        cote_equipe1 = selected_match["equipe1"]["cote"]
        cote_egalite = selected_match["X"]["cote"]
        cote_equipe2 = selected_match["equipe2"]["cote"]
        
        # Prédiction des probabilités
        result = predict_match_probability(equipe1_name, equipe2_name, model, scaler)
        
        proba_home = result.get("Home Win", 0)
        proba_away = result.get("Away Win", 0)
        proba_tie  = result.get("Tie", 0)
        
        # Calcul des ratios
        ratio_home = float(proba_home * 100) * float(cote_equipe1)
        ratio_away = float(proba_away * 100) * float(cote_equipe2)
        ratio_tie = float(proba_tie * 100) * float(cote_egalite)

        if ratio_home <= 110:
            risk_home = "risqué"
        elif ratio_home <= 140:
            risk_home = "modéré"
        elif ratio_home > 200:
            risk_home = "risqué"
        elif ratio_home > 140:
            risk_home = "safe"

        if ratio_away <= 110:
            risk_away = "risqué"
        elif ratio_away <= 140:
            risk_away = "modéré"
        elif ratio_away > 200:
            risk_away = "risqué"
        elif ratio_away > 140:
            risk_away = "safe"

        if ratio_tie <= 110:
            risk_tie = "risqué"
        elif ratio_tie <= 140:
            risk_tie = "modéré"
        elif ratio_tie > 200:
            risk_tie = "risqué"
        elif ratio_tie > 140:
            risk_tie = "safe"
        
        # Création de l'embed
        embed = discord.Embed(
            title=f"Analyse pour {equipe1_name} vs {equipe2_name}",
            color=0x3498db  # Bleu Discord (personnalisable)
        )

        embed.add_field(
            name=f"🏠 Ratio {equipe1_name}",
            value=f"**``{ratio_home:.0f}``** ¦ Risque: **``{risk_home}``**",
            inline=False
        )

        embed.add_field(
            name=f"✈️ Ratio {equipe2_name}",
            value=f"**``{ratio_away:.0f}``** ¦ Risque: **``{risk_away}``**",
            inline=False
        )

        embed.add_field(
            name="⚖️ Ratio égalité",
            value=f"**``{ratio_tie:.0f}``** ¦ Risque: **``{risk_tie}``**",
            inline=False
        )

        # Envoyer l'embed
        await interaction.response.send_message(embed=embed)
        
    except ValueError:  # Gère le split() incorrect
        await interaction.response.send_message("❌ Format de match invalide !", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message("❌ Erreur lors de la commande !", ephemeral=True)
        print(f"Erreur: {e}")

async def start_bot():
    # Charger le modèle et le scaler avant de démarrer le bot
    print("⏳ Chargement du modèle...")
    load_model_and_scaler()
    print("✅ Modèle chargé, démarrage du bot.")
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(start_bot())