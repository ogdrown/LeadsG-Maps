from playwright.sync_api import sync_playwright
import time
import urllib.parse
import os
import re

class WhatsAppBot:
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser_context = None
        self.page = None

    def start(self):
        """Inicia o navegador e abre o WhatsApp Web com sessão persistente."""
        self.playwright = sync_playwright().start()
        
        # Diretório para salvar a sessão do usuário (evita ler QR Code toda vez)
        user_data_dir = os.path.join(os.getcwd(), 'whatsapp_session')
        
        self.browser_context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=self.headless,
            # User agent ajuda a mascarar a automação
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720}
        )
        
        self.page = self.browser_context.new_page()
        print("Abrindo o WhatsApp Web...")
        self.page.goto('https://web.whatsapp.com/')
        
        print("Aguardando carregamento da interface... (Se for o primeiro acesso, escaneie o QR Code)")
        # Espera longa pela div lateral esquerda que indica que o login foi feito
        self.page.wait_for_selector('div[id="pane-side"]', timeout=90000)
        print("WhatsApp Web carregado e pronto para uso!")

    def send_message(self, phone, message):
        """
        Abre a URL de envio direto e clica no botão de enviar.
        Retorna True se enviou, False se o número for inválido ou erro de timeout.
        """
        # Limpa o número de telefone para deixar só dígitos
        phone_str = str(phone) if phone else ''
        phone_clean = re.sub(r'\D', '', phone_str)
        
        # Bloqueio Imediato: Se não tiver número ou for muito pequeno, encerra
        if len(phone_clean) < 10:
            print(f"[{phone}] Sem número ou número inválido encontrado no Google Maps. Abortando.")
            return False
            
        # Para números do Brasil, garantir o 55
        if not phone_clean.startswith('55'):
            phone_clean = '55' + phone_clean

        # Metodologia Oficial: Gerar link da API com texto pré-preenchido
        encoded_message = urllib.parse.quote(message)
        url = f"https://web.whatsapp.com/send/?phone={phone_clean}&text={encoded_message}"
        
        print(f"[{phone_clean}] Acessando aba do contato pelo Link da API...")
        
        try:
            self.page.goto(url)
            # Esperamos a janela do chat principal carregar, OU um painel de popup flutuante de alerta
            self.page.wait_for_selector('div[id="main"], div[data-testid="popup-contents"]', timeout=30000)
            time.sleep(3) # Tempo de escape do Windows para não dar enter no vazio
        except Exception as e:
            print(f"[{phone_clean}] Demora excessiva ou erro grave da página de chat.")
            self.page.goto('https://web.whatsapp.com/')
            return False
            
        try:
            # 1. Verifica se deu mensagem de inválido nativa
            invalid_elements = self.page.locator('text=inválido, text=não possui WhatsApp')
            if invalid_elements.count() > 0:
                print(f"[{phone_clean}] Número bloqueado ou não possui WhatsApp ativo na Meta.")
                self.page.keyboard.press("Escape")
                self.page.goto('https://web.whatsapp.com/') # Volta pra raiz
                return False

            # 2. Tratamento do bug da conta Business ("Iniciar Conversa" Modal)
            # Ao abrir via URL, sua conta Business pode mostrar um Popup de Iniciar na frente.
            # Vamos simplesmente ignorar e fechar a janelinha (X) se ela pipocar
            close_btn = self.page.locator('button[aria-label="Fechar"], button[title="Fechar"]')
            if close_btn.count() > 0:
                close_btn.first.click()
                time.sleep(1)
            else:
                self.page.keyboard.press("Escape")

            time.sleep(1)
            
            # 3. Dá Send no chat montado
            self.page.wait_for_selector('div[id="main"]', timeout=10000)
            self.page.keyboard.press("Enter")
            time.sleep(1.5)
            
            # Garantia do falto Enter (se o foco se perdeu)
            send_btn = self.page.locator('span[data-icon="send"]')
            if send_btn.count() > 0:
                send_btn.first.click()
            time.sleep(2)
                
            print(f"[{phone_clean}] Mensagem enviada com sucesso!")
            
            try:
                self._add_label("Novo cliente", phone_clean)
            except Exception as e:
                print(f"[{phone_clean}] Feito, mas sem etiqueta. Erro: {e}")
                
            return True

        except Exception as e:
            print(f"[{phone_clean}] Falha na tela final do WhatsApp.")
            self.page.goto('https://web.whatsapp.com/')
            return False

    def _add_label(self, label_name, curr_phone):
        """
        Adiciona uma etiqueta no contato ativo (presume que já estamos na tela do chat).
        No WA Business, clica no header do contato -> Etiquetas -> Escolhe a etiqueta e Salva.
        """
        print(f"[{curr_phone}] Tentando adicionar etiqueta '{label_name}'...")
        # Clicar no botão menu de três pontos ou direto no header do contato para info do contato
        # Uma abordagem simples é clicar no botão de menu da conversa
        menu_btn = self.page.wait_for_selector('div[data-testid="conversation-menu-button"]', timeout=3000)
        menu_btn.click()
        time.sleep(1)
        
        # Clicar na opção "Etiquetar conversa" / "Label chat"
        # O data-testid costuma ser mi-label-chat
        try:
            self.page.click('li[data-testid="mi-label-chat"]', timeout=3000)
        except:
            print("Botão de etiquetar não encontrado, verifique se seu WhatsApp é Business e se os dados da página carregaram.")
            # Fechar menu para não quebrar a UI
            self.page.keyboard.press("Escape")
            return
            
        time.sleep(1)
        
        # Procurar o checkbox/span que contém o texto da etiqueta (ex: "Novo cliente")
        # Vamos buscar um elemento que contenha o texto da etiqueta e clicar nele.
        # Caso a etiqueta já esteja marcada, não vamos desmarcar (ou podemos checar o aria-checked mas para simplificar só clicamos se não estiver).
        labels = self.page.locator(f'div[role="button"]:has-text("{label_name}")')
        if labels.count() > 0:
            # Pega o primeiro e verifica usando os checkbox internos se está "true"
            # O whatsapp usa uma div com checkbox
            checkbox = labels.first.locator('input[type="checkbox"]').first
            is_checked = checkbox.is_checked()
            
            if not is_checked:
                labels.first.click()
                time.sleep(1)
                
            # Clicar no botão Salvar
            # O botão de salvar em modais costuma ter texto 'Salvar' ou 'Save'
            save_btn = self.page.locator('button:has-text("Salvar")')
            if save_btn.count() == 0:
                 save_btn = self.page.locator('button:has-text("Save")')
                 
            if save_btn.count() > 0:
                save_btn.first.click()
                time.sleep(2)
                print(f"[{curr_phone}] Etiqueta '{label_name}' aplicada com sucesso.")
            else:
                # Fallback: tentar enviar Enter
                self.page.keyboard.press("Enter")
                time.sleep(1)
        else:
            print(f"Etiqueta '{label_name}' não encontrada na lista. Crie a etiqueta no app do celular primeiro.")
            self.page.keyboard.press("Escape")


    def close(self):
        """Fecha o navegador."""
        if self.browser_context:
            self.browser_context.close()
        if self.playwright:
            self.playwright.stop()
