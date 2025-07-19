import requests
from bs4 import BeautifulSoup

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