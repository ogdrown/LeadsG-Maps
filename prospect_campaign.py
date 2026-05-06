import time
import random
from core.storage import get_leads_to_contact, update_lead_status
from core.message_generator import MessageGenerator
from core.whatsapp_bot import WhatsAppBot
from core.site_analyzer import SiteAnalyzer

def run_campaign(max_messages=20):
    """
    Executa a campanha limitando o número de envios (ex: 20 por hora).
    Intercala checagem de respostas com novos envios.
    """
    print("="*50)
    print(" INICIANDO CAMPANHA DE PROSPECÇÃO VIA WHATSAPP ")
    print("="*50)
    
    bot = WhatsAppBot(headless=False)
    bot.start()
    
    # [1] Realizar novos disparos para leads não contatados
    print("\nEnviando prospecções...")
    leads_target = get_leads_to_contact(limit=max_messages)
    
    if not leads_target:
        print("Nenhum lead novo pendente para contatar em sua base.")
    else:
        for index, lead in enumerate(leads_target, 1):
            name = lead.get('name')
            phone = lead.get('phone')
            website = lead.get('website')
            
            print_name = name.encode('ascii', 'ignore').decode('ascii')
            print(f"\n=> ({index}/{len(leads_target)}) Processando: {print_name} | Fone: {phone}")
            
            if website and website.strip():
                print(f"[{phone}] Analisando qualidade do site atual do lead ({website})...")
                needs_improvement = SiteAnalyzer.analyze(website)
                
                if needs_improvement:
                    print(f"[{phone}] Site reprovado nos testes. Vamos tentar prospectar!")
                    message = MessageGenerator.generate_first_contact_with_website(name)
                    tipo = "COM SITE (PRECISA MELHORAR)"
                else:
                    print(f"[{phone}] Uau! Esse lead já tem um baita site. Pulando envio inteligente.")
                    update_lead_status(lead['place_id'], 'skipped_good_site')
                    continue # Pula para o próximo loop (próximo lead)
            else:
                message = MessageGenerator.generate_first_contact_no_website(name)
                tipo = "SEM SITE"
                
            print(f"Estratégia selecionada: {tipo}")
            
            success = bot.send_message(phone, message)
            
            if success:
                # Atualiza no BD para status contacted
                update_lead_status(lead['place_id'], 'contacted')
                # Obter delay randômico entre 30 e 120 segundos para evitar bloqueios anti-spam
                delay = random.randint(30, 120)
                print(f"Sucesso! Aguardando {delay} segundos antes do próximo envio (Anti-spam)...")
                time.sleep(delay)
            else:
                # Caso falhe o envio por número inválido ou timeout
                update_lead_status(lead['place_id'], 'failed')
                print("Falhou ou o cliente não tem site. Marcado como falha.")
                time.sleep(5)
                
    bot.close()
    print("\nCampanha finalizada. O bot descansará até a próxima execução.")

if __name__ == "__main__":
    run_campaign()
