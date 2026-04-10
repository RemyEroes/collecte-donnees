import requests
from bs4 import BeautifulSoup
import os

# URL de la page à scraper
URL = "https://hahnenkamm.com/en/results/result-lists-archive/"

# Dossier de téléchargement
DOWNLOAD_FOLDER = "pdf-scrapping-men"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def telecharger_fichiers():
    # Récupérer le contenu de la page
    response = requests.get(URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Trouver le tableau avec les colonnes Year, HKR-Race, Discipline, Download
    table = soup.find("table")
    if not table:
        print("Tableau non trouvé sur la page.")
        return

    rows = table.find_all("tr")

    for row in rows[1:]:  # Ignorer l'en-tête
        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        year = cells[0].text.strip()
        hkr_race = cells[1].text.strip()
        discipline = cells[2].text.strip()
        download_link = cells[3].find("a")


        if "Men" in hkr_race and "Downhill" in discipline and download_link:
            file_url = download_link["href"]
            is_second_race = '-2' if '2' in discipline else ''
            file_name = f"{year}-downhill{is_second_race}.pdf"
            file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

            # Télécharger le fichier
            print(f"Téléchargement de {file_name} depuis {file_url}...")
            with requests.get(file_url, stream=True) as file_response:
                file_response.raise_for_status()
                with open(file_path, "wb") as f:
                    for chunk in file_response.iter_content(chunk_size=8192):
                        f.write(chunk)

    print("Téléchargement terminé.")

if __name__ == "__main__":
    telecharger_fichiers()
