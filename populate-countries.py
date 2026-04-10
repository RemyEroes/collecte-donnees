import sqlite3
import json
import os

def populate_database(json_file, db_name):
    # 1. Vérifier si le fichier JSON existe
    if not os.path.exists(json_file):
        print(f"Erreur : Le fichier {json_file} est introuvable.")
        return

    try:
        # 2. Lire les données JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            countries_data = json.load(f)

        # 3. Connexion à SQLite (crée le fichier s'il n'existe pas)
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # 4. Nettoyage et création de la table
        cursor.execute("DROP TABLE IF EXISTS countries")
        cursor.execute('''
            CREATE TABLE countries (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                cca2 TEXT NOT NULL,
                cca3 TEXT NOT NULL,
                flag_url TEXT
            )
        ''')

        # 5. Préparation des données pour l'insertion groupée
        # On transforme la liste de dictionnaires en liste de tuples
        data_to_insert = [
            (c['id'], c['name'], c['cca2'], c['cca3'], c['flag'])
            for c in countries_data
        ]

        # 6. Insertion massive (plus rapide que ligne par ligne)
        cursor.executemany('''
            INSERT INTO countries (id, name, cca2, cca3, flag_url)
            VALUES (?, ?, ?, ?, ?)
        ''', data_to_insert)

        conn.commit()
        print(f"Succès ! {len(data_to_insert)} pays ont été importés dans '{db_name}'.")

    except Exception as e:
        print(f"Une erreur est survenue : {e}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    populate_database('cleaned-countries.json', 'db.sqlite')
