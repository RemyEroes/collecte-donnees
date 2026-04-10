# import sqlite3
# import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib.ticker as ticker

# def generer_graphique_performance(db_name):
#     # Connexion à la base de données
#     conn = sqlite3.connect(db_name)

#     # Requête SQL :
#     # 1. On récupère le temps du Rang 1 (MIN)
#     # 2. On calcule la moyenne des rangs 1 à 10 (AVG)
#     # On divise par 1000.0 pour passer de ms à secondes pour la lisibilité
#     query = '''
#     SELECT
#         year,
#         MIN(CASE WHEN CAST(rank AS INTEGER) = 1 THEN time_ms END) / 1000.0 as best_time,
#         AVG(CASE WHEN CAST(rank AS INTEGER) BETWEEN 1 AND 10 THEN time_ms END) / 1000.0 as avg_top10
#     FROM results
#     GROUP BY year
#     ORDER BY year
#     '''

#     # Chargement dans un DataFrame Pandas
#     df = pd.read_sql_query(query, conn)
#     conn.close()

#     if df.empty:
#         print("Aucune donnée trouvée dans la table results.")
#         return

#     # Création du graphique
#     plt.figure(figsize=(12, 6))

#     # Courbe du meilleur temps (Rang 1)
#     plt.plot(df['year'], df['best_time'], marker='o', label='Meilleur temps (Rang 1)',
#              linewidth=2, color='#1f77b4')

#     # Courbe de la moyenne Top 10
#     plt.plot(df['year'], df['avg_top10'], marker='s', linestyle='--',
#              label='Moyenne Top 10', color='#ff7f0e')

#     # Mise en forme de l'axe X pour afficher les années tous les 5 ans
#     ax = plt.gca()
#     ax.xaxis.set_major_locator(ticker.MultipleLocator(5))

#     # Conversion des secondes en minutes:secondes pour l'axe Y
#     def format_minutes_seconds(x, _):
#         minutes = int(x // 60)
#         seconds = int(x % 60)
#         return f"{minutes}:{seconds:02d}"

#     ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_minutes_seconds))

#     # Mise à jour des années affichées sur l'axe X pour ne montrer que celles multiples de 5
#     plt.xticks(df['year'][df['year'] % 5 == 0])

#     # Mise en forme
#     plt.title('Évolution des performances chronométriques par année', fontsize=14)
#     plt.xlabel('Année', fontsize=12)
#     plt.ylabel('Temps (minutes:secondes)', fontsize=12)
#     plt.legend()
#     plt.grid(True, linestyle=':', alpha=0.6)

#     # Sauvegarde et affichage
#     plt.tight_layout()
#     plt.savefig('evolution_performances.png')
#     print("Le graphique a été sauvegardé sous le nom 'evolution_performances.png'")

# if __name__ == "__main__":
#     generer_graphique_performance('db.sqlite')


import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def generer_graphique_marques_ski(db_name):
    conn = sqlite3.connect(db_name)

    # Requête SQL :
    # On récupère le meilleur temps par année ET par marque
    # Uniquement pour le Rang 1 pour voir la "vitesse de pointe" de la marque
    query = '''
    SELECT
        r.year,
        b.name as brand_name,
        MIN(r.time_ms) / 1000.0 as best_time
    FROM results r
    JOIN ski_brands b ON r.ski = b.id
    WHERE r.time_ms > 110000
    GROUP BY r.year, b.name
    ORDER BY r.year
    '''

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("Aucune donnée trouvée (vérifiez les jointures ski_brand_id).")
        return

    # Transformation des données : on veut les années en index et les marques en colonnes
    df_pivot = df.pivot(index='year', columns='brand_name', values='best_time')

    # Création du graphique
    plt.figure(figsize=(14, 8))

    # Tracer chaque marque présente dans le pivot
    for brand in df_pivot.columns:
        # On ne trace que si la marque a plus de 2 points pour faire une ligne
        data = df_pivot[brand].dropna()
        if len(data) > 0:
            plt.plot(data.index, data.values, marker='o', label=brand, linewidth=2)

    # Formatage des axes (Minutes:Secondes)
    ax = plt.gca()
    def format_ms(x, _):
        return f"{int(x // 60)}:{int(x % 60):02d}"

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_ms))

    # Axe X : un tick tous les 5 ans si la plage est grande
    years = df_pivot.index.unique()
    if len(years) > 10:
        ax.xaxis.set_major_locator(ticker.MultipleLocator(5))

    # Mise en forme
    plt.title('Meilleure performance par marque de ski', fontsize=16)
    plt.xlabel('Année', fontsize=12)
    plt.ylabel('Temps (min:sec)', fontsize=12)

    # Légende à l'extérieur si trop de marques
    plt.legend(title="Marques", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.savefig('performance_par_marque.png')
    print("Graphique sauvegardé : 'performance_par_marque.png'")

if __name__ == "__main__":
    generer_graphique_marques_ski('db.sqlite')
