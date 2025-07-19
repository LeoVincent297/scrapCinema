import requests
from bs4 import BeautifulSoup
from .utils import format_time

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