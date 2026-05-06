import argparse
import asyncio
import sys
import subprocess

def run_scraper(query, max_results):
    """Executa o scraper passando a query como subprocess."""
    print("\n" + "#"*60)
    print(" PASSO 1: BUSCANDO LEADS NO GOOGLE MAPS ".center(60, '#'))
    print("#"*60 + "\n")
    
    # Chama o main.py (Scraper original)
    cmd = [sys.executable, "main.py", *query, "--max", str(max_results)]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar a busca no Google Maps: {e}")
        sys.exit(1)

def run_whatsapp_campaign():
    """Executa o enviador de mensagens do WhatsApp."""
    print("\n" + "#"*60)
    print(" PASSO 2: INICIANDO PROSPECÇÃO NO WHATSAPP ".center(60, '#'))
    print("#"*60 + "\n")
    
    # Chama o prospect_campaign.py
    cmd = [sys.executable, "prospect_campaign.py"]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar a campanha do WhatsApp: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automação Completa: Google Maps Scraper + WhatsApp Bot Mkt")
    parser.add_argument("query", type=str, nargs='+', help="A busca exata que você faria no Google Maps (Ex: Pizzarias em Campinas)")
    parser.add_argument("--max", type=int, default=50, help="Máximo de resultados para raspar do Maps (Padrão: 50)")
    parser.add_argument("--skip-scrape", action="store_true", help="Pular a etapa de busca e ir direto pro WhatsApp")
    
    args = parser.parse_args()
    
    if not args.skip_scrape:
        run_scraper(args.query, args.max)
    else:
        print("\n=> Modo --skip-scrape ativo. Pulando a busca de novos leads.")
        
    run_whatsapp_campaign()
    
    print("\n[+] PROCESSO TOTAL CONCLUIDO COM SUCESSO! [+]")
