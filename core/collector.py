import asyncio
import time
from playwright.async_api import async_playwright
import urllib.parse

class GoogleMapsScraper:
    def __init__(self):
        self.base_url = "https://www.google.com/maps/search/"

    async def scrape(self, keyword, max_results=50):
        print(f"[*] Iniciando navegador (Scraper) para buscar: {keyword}")
        
        async with async_playwright() as p:
            # Iniciamos em modo invisível, mas se quiser ver abrindo coloque headless=False
            browser = await p.chromium.launch(headless=True)
            
            # Adicionamos locale pt-BR para garantir resultados no nosso idioma
            context = await browser.new_context(locale="pt-BR")
            page = await context.new_page()

            # Codifica a URL (ex: "Clínicas perto de São Paulo" -> "Cl%C3%ADnicas+perto+de+S%C3%A3o+Paulo")
            search_url = f"{self.base_url}{urllib.parse.quote(keyword)}"
            print(f"[*] Acessando {search_url}")
            
            await page.goto(search_url)
            
            # Espera carregar a barra lateral de resultados
            try:
                # O Google Maps muda as classes com frequência.
                # A classe .m6QErb (ou divs role="feed", "main", etc) contém os resultados.
                # Vamos esperar pelos links genéricos de empresas primeiro (elementos 'a' com href pro local)
                await page.wait_for_selector('a[href*="/maps/place/"]', timeout=10000)
            except Exception as e:
                print("[-] Nenhum resultado encontrado ou layout da página mudou. Detalhe:", e)
                await browser.close()
                return []

            # Passo 1: Fazer Scroll na barra lateral para carregar todos os resultados possíveis
            await self._scroll_sidebar(page, max_results)

            # Passo 2: Coletar Links de todos os cards
            links = await page.evaluate('''() => {
                // Pegar todos os links que levam a locais.
                const elements = document.querySelectorAll('a[href*="/maps/place/"]');
                return Array.from(elements).map(el => el.href);
            }''')

            # Filtra links duplicados
            links = list(set(links))
            print(f"[*] {len(links)} locais encontrados no mapa. Iniciando extração.")

            results = []
            
            # Passo 3: Abrir cada um e raspar os dados
            for index, url in enumerate(links[:max_results]):
                print(f"[*] Extraíndo [{index+1}/{len(links[:max_results])}]...")
                try:
                    data = await self._extract_place_data(page, url)
                    if data:
                        results.append(data)
                except Exception as e:
                    print(f"[-] Erro ao extrair link {url}: {e}")

            await browser.close()
            return results

    async def _scroll_sidebar(self, page, max_results):
        """
        No Google Maps os resultados carregam via scroll down no painel da esquerda.
        """
        print("[*] Rolando a lista de resultados...")
        
        # O seletor exato da div que tem a barra de rolagem muda muito.
        # Uma estratégia é focar em um card e apertar PageDown, ou buscar a div com `role="feed"`
        
        # Injeta uma função no JS da página pra descer até o fim várias vezes
        await page.evaluate('''async () => {
            const delay = ms => new Promise(res => setTimeout(res, ms));
            // Tenta achar o container de rolagem (geralmente é o feed principal)
            let scroller = document.querySelector('div[role="feed"]');
            
            if(!scroller) {
                // Tenta fallback para outro lugar
                const allDivs = Array.from(document.querySelectorAll('div'));
                scroller = allDivs.find(d => d.scrollHeight > d.clientHeight && d.clientHeight > 300);
            }
            
            if (scroller) {
                let lastHeight = 0;
                let scrollAttempts = 0;
                // Rola algumas vezes ou até chegar no fim
                while (scrollAttempts < 10) {
                    scroller.scrollTo(0, scroller.scrollHeight);
                    await delay(1500); // Espera carregar novos itens
                    let newHeight = scroller.scrollHeight;
                    if (newHeight === lastHeight) {
                        scrollAttempts++;
                    } else {
                        scrollAttempts = 0;
                    }
                    lastHeight = newHeight;
                }
            }
        }''')
        # Dá um tempinho extra pro site renderizar os últimos itens
        await asyncio.sleep(2)

    async def _extract_place_data(self, page, url):
        """
        Navega para a página específica da empresa e extrai os dados.
        """
        data = {
            'place_id': url.split('!1s')[-1].split('!')[0] if '!1s' in url else url, # ID unico gambiarra
            'name': None,
            'address': None,
            'phone': None,
            'website': None,
            'rating': None,
            'user_ratings_total': None,
            'opening_hours': None,
            'google_maps_url': url
        }

        await page.goto(url)
        # Espera carregar o título principal (tag h1)
        try:
            await page.wait_for_selector('h1', timeout=5000)
        except:
             return None

        # Roda um script no escopo do navegador para buscar as informações visuais
        extracted = await page.evaluate('''() => {
            const result = {};
            
            // Título H1
            const h1 = document.querySelector('h1');
            result.name = h1 ? h1.innerText : null;

            // Para pegar Endereço, Site e Telefone no Google Maps, geralmente eles usam ícones na frente.
            // O jeito mais "seguro" agora é iterar sobre os botões que tem os atributos de contato.
            
            const infoButtons = document.querySelectorAll('button[data-tooltip]');
            
            for(let btn of infoButtons){
                const tooltip = btn.getAttribute('data-tooltip') || '';
                const textInfo = btn.innerText || '';
                const ariaLabel = btn.getAttribute('aria-label') || '';
                
                // Endereço
                if(tooltip.includes('Copiar endereço') || ariaLabel.includes('Endereço:')) {
                    result.address = textInfo.trim();
                }
                
                // Telefone
                if(tooltip.includes('Copiar número de telefone') || ariaLabel.includes('Telefone:')) {
                    result.phone = textInfo.trim();
                }
            }

            // O website costuma ser um link que tem um icone de globo e termina abrindo em nova aba
            const websiteLink = Array.from(document.querySelectorAll('a')).find(a => 
                 a.getAttribute('data-tooltip') && a.getAttribute('data-tooltip').includes('Abrir website') 
                 || a.href && !a.href.includes('google.com') && a.innerText.includes('.com')
            );
            
            if(websiteLink) {
                // Preferimos pegar o texto, pq o href do google tem redirecionamento
                result.website = websiteLink.innerText || websiteLink.href; 
            }

            // Avaliação e Quantidade
            // As avaliações geralmente ficam div com aria-label do tipo "4,5 estrelas de 5 10 avaliações"
            const ariaSpan = document.querySelector('span[aria-label*="estrelas"]');
            if(ariaSpan) {
                const ariaText = ariaSpan.getAttribute('aria-label');
                try {
                    // Exemplo: "4,6 estrelas 1.234 avaliações"
                    const parts = ariaText.split('estrelas');
                    result.rating = parts[0].replace(',','.').replace(/[^0-9.]/g, ''); // 4.6
                    
                    if(parts.length > 1) {
                         const qt = parts[1].replace(/[^0-9]/g, '');
                         if(qt) result.user_ratings_total = parseInt(qt);
                    }
                } catch(e) {}
            }

            return result;
        }''')
        
        # Merge com nosso dict oficial
        for key in extracted:
            if extracted[key]:
                data[key] = extracted[key]

        return data
