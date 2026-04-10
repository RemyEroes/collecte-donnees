import sqlite3
import json
import os
import ollama
import re

# Configuration
BRAND_LIST = [
    "Rossignol", "Salomon", "Dynastar", "Black Crows", "Atomic",
    "Fischer", "Head", "Blizzard", "Kästle", "Völkl", "Stöckli",
    "Faction", "Nordica", "Elan", "K2", "Armada", "Line Skis"
]

def split_name_with_ai(full_name):
    prompt = (
        f"Analyse le nom : '{full_name}'. "
        "Réponds uniquement en JSON : {'prénom': '...', 'nom_famille': '...'}"
    )
    try:
        response = ollama.chat(
            model='qwen2.5:1.5b',
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        return json.loads(response['message']['content'])
    except Exception:
        return {"prénom": full_name, "nom_famille": ""}

def get_or_create_athlete(cursor, entry):
    """Récupère l'ID de l'athlète ou le crée s'il n'existe pas."""
    raw_name = entry.get('name')
    fis_code = entry.get('fis_code')
    year_birth = entry.get('year_birth')

    if not fis_code or str(fis_code).lower() == 'null':
        fis_code = None

    # 1. Recherche par FIS Code
    if fis_code:
        cursor.execute("SELECT id FROM athletes WHERE fis_code = ?", (fis_code,))
        res = cursor.fetchone()
        if res: return res[0]

    # 2. Si non trouvé, on utilise l'IA pour séparer le nom
    name_parts = split_name_with_ai(raw_name)
    fn = name_parts.get('prénom', '').strip()
    ln = name_parts.get('nom_famille', '').strip()

    # 3. Tentative de récupération par Nom/Prénom/Année
    cursor.execute(
        "SELECT id FROM athletes WHERE first_name=? AND last_name=? AND year_of_birth=?",
        (fn, ln, year_birth)
    )
    res = cursor.fetchone()
    if res: return res[0]

    # 4. Création de l'athlète (Récupération ID pays au passage)
    cc = entry.get('country_code')
    cursor.execute("SELECT id FROM countries WHERE cca3=? OR cca2=?", (cc, cc))
    country_res = cursor.fetchone()
    cid = country_res[0] if country_res else None

    cursor.execute('''
        INSERT INTO athletes (first_name, last_name, year_of_birth, country, fis_code)
        VALUES (?, ?, ?, ?, ?)
    ''', (fn, ln, year_birth, cid, fis_code))
    return cursor.lastrowid

def convertir_temps(temps):
    if not temps or str(temps).lower() == "null":
        return None
    try:
        # 1. On harmonise tous les séparateurs en ":"
        t = re.sub(r"[,.']", ":", str(temps))
        parts = [p for p in t.split(':') if p]


        if len(parts) == 3:
            # Cas fréquent en sport : Minutes : Secondes : Centièmes
            # On convertit tout en flottants
            m, s, c = map(float, parts)
            # Si 'c' est sur deux chiffres (ex: 01), c'est des centièmes (c/100)
            # On ajuste selon la logique de vos données
            total_sec = (m * 60) + s + (c / 100 if c < 100 else c / 1000)
        elif len(parts) == 2:
            m, s = map(float, parts)
            total_sec = (m * 60) + s
        else:
            total_sec = float(parts[0])

        return int(total_sec * 1000)
    except (ValueError, IndexError):
        return None

def process_files(folder_path, db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    for filename in sorted(os.listdir(folder_path)):
        if not filename.endswith('.json'): continue

        file_path = os.path.join(folder_path, filename)
        year_event = filename.split(".")[0]

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            entries = data if isinstance(data, list) else [data]

            for entry in entries:
                # ÉTAPE 1 : Obtenir l'ID Athlète (Unique)
                athlete_id = get_or_create_athlete(cursor, entry)

                # ÉTAPE 2 : Gérer la marque de ski
                ski_txt = entry.get("ski", "")
                brand_id = None
                if ski_txt:
                    brand = next((b for b in BRAND_LIST if b.lower() in ski_txt.lower()), None)
                    if brand:
                        cursor.execute("SELECT id FROM ski_brands WHERE name=?", (brand,))
                        res = cursor.fetchone()
                        brand_id = res[0] if res else None

                # ÉTAPE 3 : Insérer le résultat
                cursor.execute('''
                    INSERT INTO results (athlete, year, time_ms, rank, distance_m, points, ski)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (athlete_id, year_event, convertir_temps(entry.get("time_raw")),
                      entry.get("rank"), entry.get("distance"), entry.get("points"), brand_id))

            conn.commit()
            print(f"Importé : {filename}")

    conn.close()

if __name__ == "__main__":
    process_files('resultats-qwen', 'db.sqlite')
