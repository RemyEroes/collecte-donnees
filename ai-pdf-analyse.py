import ollama
from pypdf import PdfReader
import json
import re

def extraire_texte_pdf(chemin_pdf):
    """Lit le PDF et extrait tout le texte."""
    reader = PdfReader(chemin_pdf)
    texte_complet = ""
    for page in reader.pages:
        texte_complet += page.extract_text() + "\n"
    return texte_complet

def temps_en_centiemes(temps_str):
    """Convertit '1:52.31' ou '0.07' ou '52.31' en centièmes (entier)."""
    if not temps_str or not isinstance(temps_str, str) or temps_str.strip() == "":
        return None

    # Nettoyage des caractères parasites
    temps_str = temps_str.replace(',', '.').strip()

    try:
        if ':' in temps_str:
            minutes, secondes = temps_str.split(':')
            total_secondes = (int(minutes) * 60) + float(secondes)
        else:
            total_secondes = float(temps_str)

        return int(round(total_secondes * 100))
    except ValueError:
        return None

def analyser_avec_qwen(texte):
    """Envoie le texte à Qwen 2.5 via Ollama pour extraire le JSON."""

    prompt = """
    Tu es un expert en extraction de données. Je vais te donner le texte brut des résultats officiels d'une course de ski FIS.
    Ton objectif est d'extraire le classement sous forme de tableau JSON.

    Règles strictes :
    1. Renvoie UNIQUEMENT un tableau (array) d'objets JSON. Rien d'autre.
    2. Si une information est absente, mets la valeur `null` c'est très important.
    3. Les clés doivent être exactement celles demandées, sans faute de frappe ni variation.
    4. Ne pas inclure de texte explicatif, de commentaires ou de métadonnées. Juste le JSON.
    5. Ne garde que les finishers (skieurs classés), ignore les DNF, DSQ, etc.

    Pour chaque skieur, extrais les clés exactes suivantes :
    - "rank" (entier)
    - "bib" (entier, c'est le numéro de dossard)
    - "fis_code" (chaine de caractères)
    - "name" (chaine de caractères mettre le nom en MAJUSCULES)
    - "year_birth" (entier)
    - "country_code" (chaine de 3 lettres, ex: "FRA", "SUI")
    - "time_raw" (temps en centièmes de seconde entier, ex: pour "1:52.31" on mettra 11231)
    - "diff_raw" (temps en centièmes de seconde entier, ex: pour "0.07" on mettra 7)
    - "distance" (float, en mètres)
    - "points" (float, points de course)
    - "ski" (chaine de caractères, la marque des skis, ex: "Rossignol")

    Voici le texte à analyser :
    """ + texte

    print("Envoi du texte à Qwen 2.5 (1.5B)... Cela peut prendre quelques secondes.")

    # Appel à l'API locale d'Ollama
    reponse = ollama.chat(
        model='qwen2.5:1.5b',
        messages=[
            {'role': 'user', 'content': prompt}
        ],
        format='json' # Force Ollama à ne sortir que du JSON valide
    )

    print("Réponse brute de Qwen 2.5 reçue. Tentative de parsing JSON...")
    print(reponse['message']['content'])

    return reponse['message']['content']

def traiter_fichier(chemin_pdf):
    # 1. Lire le PDF
    texte_pdf = extraire_texte_pdf(chemin_pdf)

    # 2. Extraire le JSON brut avec l'IA
    json_brut = analyser_avec_qwen(texte_pdf)

    try:
        data = json.loads(json_brut)
    except json.JSONDecodeError:
        print("Erreur: Le modèle n'a pas renvoyé un JSON valide.")
        print(json_brut)
        return

    # --- CORRECTION ICI : Rendre le code tolérant au format de l'IA ---
    # Si l'IA a renvoyé un dictionnaire au lieu d'une liste directement
    if isinstance(data, dict):
        # On récupère la première clé (par ex: "resultats", "skieurs", etc.)
        premiere_cle = list(data.keys())[0]
        data = data[premiere_cle]
        print(f"Info : Les données étaient encapsulées dans la clé '{premiere_cle}'")

    # Sécurité supplémentaire
    if not isinstance(data, list):
        print("Erreur : Impossible de trouver une liste de skieurs dans le JSON généré.")
        print("Voici ce que l'IA a renvoyé :", data)
        return

    # Vérification supplémentaire pour éviter les erreurs si data est un entier
    if isinstance(data, int):
        print("Erreur : Les données renvoyées ne sont pas valides. Attendu une liste de skieurs.")
        return

    # -----------------------------------------------------------------

    # 3. Post-traitement Python (Conversion des temps en centièmes)
    resultats_finaux = []
    for skieur in data:
        # Sécurité : vérifier que l'élément est bien un dictionnaire
        if not isinstance(skieur, dict):
            continue

        # Conversion du chrono
        skieur["time"] = temps_en_centiemes(skieur.get("time_raw"))
        skieur["diff"] = temps_en_centiemes(skieur.get("diff_raw"))

        # Nettoyage des clés temporaires
        skieur.pop("time_raw", None)
        skieur.pop("diff_raw", None)

        resultats_finaux.append(skieur)

    # 4. Sauvegarde
    fichier_sortie = "resultats_qwen.json"
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        json.dump(resultats_finaux, f, ensure_ascii=False, indent=4)

    print(f"Succès ! {len(resultats_finaux)} skieurs extraits et sauvegardés dans {fichier_sortie}")

if __name__ == "__main__":
    # Assurez-vous que le chemin vers votre PDF est correct
    mon_pdf = "pdf/2026.pdf"
    traiter_fichier(mon_pdf)
