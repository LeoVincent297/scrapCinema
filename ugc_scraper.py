import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import pandas as pd
import xlsxwriter
from ugc_modules import format_time, get_seances_for_film, get_films_info, export_to_excel

def main():
    # Récupérer la liste des films
    films = get_films_info()
    if not films:
        print("Impossible de récupérer la liste des films")
        return

    # Préparer les dates
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    today_str = today.strftime('%Y-%m-%d')
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')

    print(f"Dates de recherche : {today_str} et {tomorrow_str}")

    # Structure pour les résultats
    results = {
        "date_extraction": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "categories": {}
    }

    # Pour chaque film, récupérer les séances
    for film in films:
        print(f"\nTraitement du film : {film['titre']}")
        film_data = {
            "id": film["id"],
            "titre": film["titre"],
            "url": film["url"],
            "cinemas": {}
        }

        if "label" in film:
            film_data["label"] = film["label"]
        if "genre" in film:
            film_data["genre"] = film["genre"]

        # Récupérer les séances
        seances_today = get_seances_for_film(film["id"], film["titre"], today_str, "aujourd'hui")
        seances_tomorrow = get_seances_for_film(film["id"], film["titre"], tomorrow_str, "demain")

        # Ne traiter que les cinémas qui ont des séances
        all_cinemas = set(list(seances_today.keys()) + list(seances_tomorrow.keys()))
        for cinema in all_cinemas:
            film_data["cinemas"][cinema] = {
                "adresse": seances_today.get(cinema, seances_tomorrow.get(cinema))["adresse"],
                "seances": []
            }

            # Ajouter les séances d'aujourd'hui et de demain
            if cinema in seances_today:
                film_data["cinemas"][cinema]["seances"].extend(seances_today[cinema]["seances"])
            if cinema in seances_tomorrow:
                film_data["cinemas"][cinema]["seances"].extend(seances_tomorrow[cinema]["seances"])

            # Trier les séances par date et heure
            film_data["cinemas"][cinema]["seances"].sort(key=lambda x: (x["date"], x["heure_debut"]))

            # Si pas de séances pour ce cinéma, le retirer
            if not film_data["cinemas"][cinema]["seances"]:
                del film_data["cinemas"][cinema]

        # N'ajouter le film que s'il a des séances
        if film_data["cinemas"]:
            # Déterminer la catégorie
            categorie = "Autres"
            if "genre" in film_data:
                categorie = film_data["genre"]
            elif "label" in film_data:
                categorie = film_data["label"]

            # Créer la catégorie si elle n'existe pas
            if categorie not in results["categories"]:
                results["categories"][categorie] = []
            
            # Ajouter le film à sa catégorie
            results["categories"][categorie].append(film_data)
    
    # Trier les films par titre dans chaque catégorie
    for categorie in results["categories"]:
        results["categories"][categorie].sort(key=lambda x: x["titre"])
    
    # Sauvegarder en JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = f'ugc_films_seances_{timestamp}.json'
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nLes informations ont été sauvegardées dans {json_file}")
    
    # Exporter en Excel
    excel_file = export_to_excel(results)
    
    # Afficher le résumé
    total_films = sum(len(films) for films in results["categories"].values())
    print(f"\nRésumé : {total_films} films avec des séances trouvés")
    
    for categorie, films in results["categories"].items():
        print(f"\n=== {categorie} ({len(films)} films) ===")
        for film in films:
            print(f"\n{film['titre']}")
            for cinema, info in film["cinemas"].items():
                print(f"\n  {cinema}")
                print(f"  {info['adresse']}")
                
                # Grouper les séances par jour
                seances_by_day = {}
                for seance in info["seances"]:
                    if seance["date"] not in seances_by_day:
                        seances_by_day[seance["date"]] = []
                    seances_by_day[seance["date"]].append(seance)
                
                # Afficher les séances par jour
                for jour, seances in seances_by_day.items():
                    seances_str = [f"{s['heure_debut']} ({s['version']}{' - ' + s['salle'] if s['salle'] else ''})" 
                                 for s in seances]
                    print(f"    {jour.capitalize()}: {', '.join(seances_str)}")

if __name__ == '__main__':
    main() 
