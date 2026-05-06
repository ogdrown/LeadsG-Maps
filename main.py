import asyncio
import argparse
from core.storage import init_db, save_lead, get_lead_count
from core.collector import GoogleMapsScraper
from core.processor import process_place

async def main():
    parser = argparse.ArgumentParser(description="Google Maps Leads Extractor (Web Scraper)")
    parser.add_argument("query", type=str, nargs='+', help="A busca exata que você faria no Google Maps (Ex: Clínicas odontológicas em São Paulo)")
    parser.add_argument("--max", type=int, default=50, help="Máximo de resultados para tentar raspar (Padrão: 50)")
    
    args = parser.parse_args()
    keyword = " ".join(args.query)

    print(f"[*] Iniciando Google Maps Leads Extractor (Scraper Mode)")
    print(f"[*] Buscando por: '{keyword}'")
    
    # 1. Init DB
    print("[*] Inicializando banco de dados local...")
    init_db()
    
    # 2. Init Collector
    scraper = GoogleMapsScraper()

    # 3. Faz a busca e a raspagem
    places_scraped = await scraper.scrape(keyword, args.max)
    
    total_found = len(places_scraped)
    total_saved = 0
    total_com_site = 0

    print("[*] Processando e filtrando...")
    for p in places_scraped:
        # Processa (filtra quem tem site e formata)
        lead_data = process_place(p, keyword)
        
        if lead_data:  # Passou no filtro (não tem site)
            saved = save_lead(lead_data)
            lead_name_safe = str(lead_data.get('name', '')).encode('ascii', errors='replace').decode('ascii')
            if saved:
                total_saved += 1
                print(f"[+] Salvo: {lead_name_safe} (Tel: {lead_data.get('phone')})")
                print(f"    Link: {lead_data.get('google_maps_url')}")
            else:
                print(f"[-] Ignorado: {lead_name_safe} (Já existe na base)")
        else:
            total_com_site += 1
                
    # Final summary
    leads_after = get_lead_count()
    print("\n" + "="*40)
    print("RESUMO DA EXTRAÇÃO")
    print("="*40)
    print(f"Locais raspados do mapa: {total_found}")
    print(f"Empresas COM site (Descartadas): {total_com_site}")
    print(f"Total leads salvos nesta execução: {total_saved}")
    print(f"Total de leads no Banco (Global): {leads_after}")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(main())
