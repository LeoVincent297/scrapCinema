import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import pandas as pd
import xlsxwriter

def format_time(time_str):
    return datetime.strptime(time_str.strip(), '%H:%M').strftime('%Hh%M')

def get_seances_for_film(film_id, film_title, date_str, jour_label):
    base_url = "https://www.ugc.fr/showingsFilmAjaxAction!getShowingsByFilm.action"
    url = f"{base_url}?regionId=1&filmId={film_id}&day={date_str}"
    
    headers = {
        'User-Agent': 'Scraping-Bot (contact: Vincentleo105@gmail.com)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    print(f"Récupération des séances pour {film_title} - {jour_label}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Erreur: status code {response.status_code}")
        return {}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    seances = {}
    
    cinemas = soup.find_all('div', class_='band component--cinema-list-item')
    
    for cinema_section in cinemas:
        cinema_title = cinema_section.find('a', class_='color--dark-blue')
        if not cinema_title:
            continue
        
        cinema_name = cinema_title.get_text(strip=True)
        address = cinema_section.find('p', class_='address')
        if not address:
            continue
            
        address_text = address.get_text(strip=True)
        if '75' not in address_text:
            continue
            
        if cinema_name not in seances:
            seances[cinema_name] = {
                "adresse": address_text,
                "seances": []
            }
        
        seance_section = cinema_section.find_all('div', class_='col-md-5')[1] if len(cinema_section.find_all('div', class_='col-md-5')) > 1 else None
        if seance_section:
            seances_items = seance_section.find_all('button', class_='bg--main-blue')
            
            for seance in seances_items:
                start_time = seance.find('div', class_='screening-start')
                version = seance.find('span', class_='screening-lang')
                salle = seance.find('div', class_='screening-detail')
                end_time = seance.find('div', class_='screening-end')
                
                if start_time:
                    horaire = {
                        "date": jour_label,
                        "heure_debut": format_time(start_time.get_text(strip=True)),
                        "heure_fin": end_time.get_text(strip=True).strip('()') if end_time else "",
                        "version": version.get_text(strip=True) if version else "VF",
                        "salle": salle.get_text(strip=True) if salle else ""
                    }
                    seances[cinema_name]["seances"].append(horaire)
    
    return seances

def get_films_info():
    BASE_URL = "https://www.ugc.fr"
    url = f"{BASE_URL}/filmsAjaxAction!getFilmsAndFilters.action?filter=&page=30010&cinemaId=&reset=false&"
    
    headers = {
        'User-Agent': 'Scraping-Bot (contact: Vincentleo105@gmail.com)',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3'
    }
    
    try:
        print("Récupération de la liste des films...")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f'Erreur lors de la requête. Code status: {response.status_code}')
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        films_data = {}  # Utiliser un dictionnaire pour éviter les doublons
        
        film_tiles = soup.find_all('div', class_='component--film-tile')
        print(f"Nombre de films trouvés : {len(film_tiles)}")
        
        for film_tile in film_tiles:
            visu_wrapper = film_tile.find('div', class_='visu-wrapper')
            if not visu_wrapper:
                continue
                
            link_elem = visu_wrapper.find('a', href=lambda x: x and x.startswith('film_'))
            
            if link_elem:
                title = link_elem.get('title', '').strip()
                if title and not any(mot in title.lower() for mot in ['ugc', 'inscrivez', 'séances', 'cinéma', 'mag']):
                    link_id = link_elem.get('id', '')
                    if link_id.startswith('goToFilm_'):
                        film_id = link_id.split('_')[1].split('_')[0]
                        href = link_elem['href']
                        link = f"{BASE_URL}/{href}"
                        
                        # Utiliser l'ID comme clé pour éviter les doublons
                        if film_id not in films_data:
                            film_info = {
                                "id": film_id,
                                "titre": title,
                                "url": link,
                                "cinemas": {}
                            }
                            
                            label_elem = visu_wrapper.find('span', class_='film-tag')
                            if label_elem:
                                film_info["label"] = label_elem.get_text(strip=True)
                            
                            genre = link_elem.get('data-film-kind', '').strip()
                            if genre:
                                film_info["genre"] = genre
                            
                            films_data[film_id] = film_info
                            print(f"Film ajouté : {title} (ID: {film_id})")
        
        return list(films_data.values())
    
    except Exception as e:
        print(f'Erreur: {e}')
        import traceback
        traceback.print_exc()
        return None

def export_to_excel(results):
    data = []

    # Parcourir les catégories
    for categorie, films in results["categories"].items():
        for film in films:
            for cinema, info in film["cinemas"].items():
                for seance in info["seances"]:
                    row = {
                        "Catégorie": categorie,
                        "Film": film["titre"],
                        "Genre": film.get("genre", ""),
                        "Label": film.get("label", ""),
                        "Cinéma": cinema,
                        "Adresse": info["adresse"],
                        "Date": seance["date"],
                        "Heure": seance["heure_debut"],
                        "Version": seance["version"],
                        "Salle": seance["salle"],
                        "URL": film["url"]
                    }
                    data.append(row)

    # Créer les DataFrames triés
    df_by_type = pd.DataFrame(data).sort_values(by=["Catégorie", "Film", "Cinéma", "Date", "Heure"])
    df_by_film = pd.DataFrame(data).sort_values(by=["Film", "Cinéma", "Date", "Heure"])

    # Nom du fichier
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_file = f'ugc_films_seances_{timestamp}.xlsx'

    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        df_by_type.to_excel(writer, sheet_name='Par catégorie', index=False)
        df_by_film.to_excel(writer, sheet_name='Par film', index=False)

        workbook = writer.book
        formats = {
            "header": workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'top',
                'bg_color': '#D9E1F2', 'border': 1
            }),
            "cell": workbook.add_format({
                'text_wrap': True, 'valign': 'top', 'border': 1
            })
        }

        for sheet_name in ['Par catégorie', 'Par film']:
            worksheet = writer.sheets[sheet_name]

            for col_num, value in enumerate(df_by_type.columns.values):
                worksheet.write(0, col_num, value, formats["header"])

            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:B', 30)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('D:D', 15)
            worksheet.set_column('E:E', 25)
            worksheet.set_column('F:F', 35)
            worksheet.set_column('G:G', 12)
            worksheet.set_column('H:H', 10)
            worksheet.set_column('I:I', 10)
            worksheet.set_column('J:J', 10)
            worksheet.set_column('K:K', 50)

            worksheet.freeze_panes(1, 0)
            worksheet.autofilter(0, 0, len(data), len(df_by_type.columns) - 1)

    print(f"\nLes informations ont été exportées dans {excel_file}")
    return excel_file 