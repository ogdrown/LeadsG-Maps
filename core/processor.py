def process_place(place_data, keyword):
    """
    Recebe os dados raspados pelo Playwright e os prepara para o formato do banco de dados.
    Verifica se o local possui website. Se tiver, retorna None.
    """
    website = place_data.get('website')
    

    # Tratamento básico de campos vazios ou não encontrados
    name = place_data.get('name')
    if not name:
        return None # Sem nome é inútil

    return {
        'place_id': place_data.get('place_id') or str(hash(name)), # fallback de ID
        'name': name,
        'address': place_data.get('address'),
        'phone': place_data.get('phone'),
        'email': None, # Scraper não pega email
        'website': website,
        'rating': place_data.get('rating'),
        'user_ratings_total': place_data.get('user_ratings_total'),
        'opening_hours': place_data.get('opening_hours'),
        'category': keyword,
        'search_radius': 0, # Scraper usa queries abertas, não raio exato
        'google_maps_url': place_data.get('google_maps_url')
    }
