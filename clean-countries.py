import json
import ollama

def fix_encoding(text):
    """Répare les erreurs d'encodage communes (ex: Cà´te -> Côte)"""
    if not text:
        return text
    try:
        # On tente de réparer le texte mal encodé
        return text.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Si ça échoue, on retourne le texte tel quel ou avec des remplacements manuels
        replacements = {
            "Cà´te": "Côte",
            "PolynÃ©sie": "Polynésie",
            "FranÃ§aise": "Française"
        }
        for key, val in replacements.items():
            text = text.replace(key, val)
        return text

def get_cca3_from_ai(country_name):
    """Demande à l'IA de trouver le code ISO Alpha-3"""
    prompt = f"Donne-moi uniquement le code ISO 3166-1 alpha-3 pour le pays suivant : {country_name}. Réponds par un seul mot de 3 lettres."
    response = ollama.chat(model='qwen2.5:1.5b', messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content'].strip().upper()

# 1. Chargement des données
# On suppose que ton dataset principal est dans 'countries_data.json'
with open('countries/countries.json', 'r', encoding='utf-8') as f:
    countries_list = json.load(f)

# Chargement du fichier cca2.json (ex: {"ad": "Andorra", "fr": "France"})
with open('countries/cca2.json', 'r', encoding='utf-8') as f:
    cca2_map = json.load(f)
    # On inverse le dictionnaire pour chercher par nom : {"Andorra": "ad"}
    name_to_cca2 = {name.lower(): code.lower() for code, name in cca2_map.items()}

final_dataset = []

# 2. Traitement des données
for index, item in enumerate(countries_list, start=1):
    # Récupération et nettoyage du nom
    raw_name = item.get("name", {}).get("common", "Unknown")
    clean_name = fix_encoding(raw_name)

    # Recherche du CCA2
    # On cherche le nom nettoyé dans notre map inversée
    cca2 = name_to_cca2.get(clean_name.lower(), "??")

    # Récupération du CCA3 via Ollama
    print(f"Traitement : {clean_name}...")
    cca3 = get_cca3_from_ai(clean_name)

    # Construction du nouvel objet
    country_obj = {
        "id": index,
        "name": clean_name,
        "cca2": cca2,
        "cca3": cca3,
        "flag": f"https://flagcdn.com/{cca2}.svg" if cca2 != "??" else None
    }

    final_dataset.append(country_obj)

# 3. Sauvegarde du résultat
with open('countries_final.json', 'w', encoding='utf-8') as f:
    json.dump(final_dataset, f, indent=2, ensure_ascii=False)

print("\nOpération terminée ! Le fichier countries_final.json a été créé.")
