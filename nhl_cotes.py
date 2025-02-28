from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

# Configurer Selenium avec Chrome
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 5)

# URL cible
url = "https://jeux.loro.ch/sports/hub/811856"
driver.get(url)

# Attendre que la page se charge complètement (optionnel)
driver.implicitly_wait(5)

# Récupérer le HTML complet
html = driver.page_source

fichier = open("cotes.txt", "w", encoding="utf-8")
fichier.write(str(html))
fichier.close()

# Fermer le navigateur
driver.quit()