import sqlite3
import json
import os

def populate_ski_brands(json_file, db_name):
    if not os.path.exists(json_file):
        print(f"Erreur : Le fichier {json_file} est introuvable.")
        return

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 1. Création de la table ski_brands
    # origin_country stockera l'ID provenant de la table countries
    cursor.execute("DROP TABLE IF EXISTS ski_brands")
    cursor.execute('''
        CREATE TABLE ski_brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            origin_country_id INTEGER,
            FOREIGN KEY (origin_country_id) REFERENCES countries (id)
        )
    ''')

    # 2. Chargement du JSON des marques
    with open(json_file, 'r', encoding='utf-8') as f:
        brands_data = json.load(f)

    print("Début de l'importation des marques...")

    brands_imported = 0
    for item in brands_data:
        brand_name = item['brand']
        cca3_code = item['cca3']

        # 3. Recherche de l'ID du pays dans la table 'countries' via le CCA3
        cursor.execute("SELECT id FROM countries WHERE cca3 = ?", (cca3_code,))
        result = cursor.fetchone()

        if result:
            country_id = result[0]
            # 4. Insertion dans la table ski_brands
            cursor.execute('''
                INSERT INTO ski_brands (name, origin_country_id)
                VALUES (?, ?)
            ''', (brand_name, country_id))
            brands_imported += 1
        else:
            print(f"⚠️ Pays non trouvé pour la marque {brand_name} (CCA3: {cca3_code})")

    conn.commit()
    conn.close()
    print(f"Terminé ! {brands_imported} marques ont été liées et importées.")

if __name__ == "__main__":
    # Assure-toi que le nom de la base correspond à celui utilisé précédemment
    populate_ski_brands('ski-brand.json', 'db.sqlite')
