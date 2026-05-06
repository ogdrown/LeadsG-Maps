import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time

class SiteAnalyzer:
    """
    Analisa a qualidade heurística de um site para determinar se ele já é 'bom'
    ou se tem margem para melhoria (potencial cliente).
    """
    
    @staticmethod
    def _normalize_url(url):
        if not url.startswith('http'):
            return 'http://' + url
        return url

    @classmethod
    def analyze(cls, url):
        """
        Gera uma pontuação para o site e retorna True se ele precisa de melhorias,
        False se considerar o site 'Foda' (não mandar mensagem de prospecção).
        """
        if not url or len(url.strip()) < 4:
            return True # Trata como sem site

        url = cls._normalize_url(url)
        score = 0
        max_score = 100
        
        try:
            # 1. Teste de tempo de resposta e HTTPS
            # Sites profissionais costumam carregar rápido e ter HTTPS forçado
            start_time = time.time()
            response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            load_time = time.time() - start_time
            
            # Penaliza muito se não for HTTPS após redirecionamento
            if response.url.startswith('https'):
                score += 30
            else:
                score -= 20
                
            # Verifica a velocidade (em segundos)
            if load_time < 2.0:
                score += 20
            elif load_time < 5.0:
                score += 10
            else:
                score -= 10 # Site lento
                
            # 2. Teste de estrutura HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Verifica responsividade básica (meta viewport) - Indispensável hoje em dia
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            if viewport:
                score += 25
            else:
                score -= 30 # Site muito antigo
                
            # Verifica quantidade de conteúdo (Landing pages modernas costumam ter bastante info/imagens)
            text_length = len(soup.get_text(separator=' ', strip=True))
            if text_length > 1000:
                score += 15
            elif text_length < 200:
                score -= 10 # Site quase vazio (Link tree, etc)
                
            # Verifica imagens
            images = soup.find_all('img')
            if len(images) > 3:
                score += 10
                
            print(f"[{url}] Load: {load_time:.1f}s | HTTPS: {response.url.startswith('https')} | Viewport: {bool(viewport)} => Score Final: {score}")

            # Define a nota de corte (Mínimo para ser um site aceitável/bom)
            # Acima de 60 consideramos q ele tem um bom site e PULA.
            # Abaixo de 60 consideramos ruim e mandamos msg.
            if score >= 60:
                return False # Não precisa de melhoria imperativa ("Site Foda")
            else:
                return True # Precisa melhorar ("Site Ruim")
                
        except requests.RequestException as e:
            # Se deu timeout, SSL Error, DNS Error... o site está quebrado/fora do ar.
            # Precisamos muito vender um site pra ele!
            print(f"[{url}] Erro de acesso ({type(e).__name__}). Considerado 'Site Ruim'")
            return True
        except Exception as e:
             # Para outros erros, peca pelo excesso e manda mensagem
             print(f"[{url}] Erro na analise. Considerado 'Site Ruim'")
             return True
