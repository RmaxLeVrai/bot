from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import json

# Dictionnaire de correspondance pour les noms d'équipes
TEAM_MAPPING = {
    "Anaheim": "Ducks",
    "Arizona": "Coyotes",
    "Boston": "Bruins",
    "Buffalo": "Sabres",
    "Calgary": "Flames",
    "Carolina": "Hurricanes",
    "Chicago": "Blackhawks",
    "Colorado": "Avalanche",
    "Colombus": "Blue Jackets",  # Note: Faute de frappe probable ("Columbus")
    "Dallas": "Stars",
    "Detroit": "Red Wings",
    "Edmonton": "Oilers",
    "Florida": "Panthers",
    "Los Angeles": "Kings",
    "Minnesota": "Wild",
    "Montreal": "Canadiens",
    "Nashville": "Predators",
    "New Jersey": "Devils",
    "NY Islanders": "Islanders",
    "NY Rangers": "Rangers",
    "Ottawa": "Senators",
    "Philadelphia": "Flyers",
    "Pittsburgh": "Penguins",
    "San Jose": "Sharks",
    "Seattle": "Kraken",
    "St. Louis": "Blues",
    "Tampa Bay": "Lightning",
    "Toronto": "Maple Leafs",
    "Vancouver": "Canucks",
    "Vegas": "Golden Knights",
    "Washington": "Capitals",
    "Winnipeg": "Jets"
}

# Configurer Selenium avec Chrome
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 6)

# URL cible
url = "https://jeux.loro.ch/sports/hub/811856"
driver.get(url)

# Attendre que la page se charge complètement (optionnel)
driver.implicitly_wait(6)

# Récupérer le HTML complet
html = driver.page_source

fichier = open("cotes2.txt", "w", encoding="utf-8")
fichier.write(str(html))
fichier.close()

# Fermer le navigateur
driver.quit()

with open("cotes2.txt", "r", encoding="utf-8") as file:
    html_content = file.read()

# Parser le contenu HTML avec BeautifulSoup
soup = BeautifulSoup(html_content, "lxml")

# Extraire toutes les balises ayant la classe spécifique
cotes = soup.find_all("span", class_="button-coeff active css-o5sfjm")
names = soup.find_all("span", class_="button-name")

# Vérifier que les deux listes ont la même longueur
if len(cotes) != len(names):
    print("Les listes de cotes et de noms n'ont pas la même longueur.")
else:
    # Créer une liste de tuples (cote, nom)
    associations = list(zip([button.text.strip() for button in cotes], [button.text.strip() for button in names]))

    # Créer une liste pour stocker les matchs
    matches = []

    # Parcourir les associations par groupes de 3 (équipe1, X, équipe2)
    for i in range(0, len(associations), 3):
        if i + 2 < len(associations):  # Vérifier qu'il y a bien 3 éléments pour un match
            equipe1 = associations[i]
            x = associations[i + 1]
            equipe2 = associations[i + 2]

            # Créer un dictionnaire pour le match
            match = {
                "equipe1": {
                    "nom": equipe1[1],
                    "cote": equipe1[0]
                },
                "X": {
                    "nom": x[1],
                    "cote": x[0]
                },
                "equipe2": {
                    "nom": equipe2[1],
                    "cote": equipe2[0]
                }
            }

            # Ajouter le match à la liste des matchs
            matches.append(match)

    # Écrire les matchs dans un fichier JSON
    with open("matches.json", "w", encoding="utf-8") as json_file:
        json.dump(matches, json_file, ensure_ascii=False, indent=4)

    print("Les matchs ont été écrits dans le fichier matches.json")


# Lire le fichier JSON existant
with open("matches.json", "r", encoding="utf-8") as json_file:
    matches = json.load(json_file)

# Mettre à jour les noms des équipes
for match in matches:
    for side in ["equipe1", "equipe2"]:
        old_name = match[side]["nom"]
        # Appliquer la correspondance ou garder le nom original s'il n'y a pas de correspondance
        match[side]["nom"] = TEAM_MAPPING.get(old_name, old_name)

# Réécrire le fichier JSON avec les noms standardisés
with open("matches_updated.json", "w", encoding="utf-8") as json_file:
    json.dump(matches, json_file, ensure_ascii=False, indent=4)

# Générer la liste au format [Équipe1 vs Équipe2]
match_list = [f"{match['equipe1']['nom']} vs {match['equipe2']['nom']}" for match in matches]

print("Noms standardisés et liste générée :")
print(match_list)