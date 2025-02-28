from bs4 import BeautifulSoup

# Charger le fichier HTML
file_path = "cotes.txt"

with open(file_path, "r", encoding="utf-8") as file:
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

    # Afficher les associations
    for cote, name in associations:
        print(f"{cote} : {name}")