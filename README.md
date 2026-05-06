# Google Maps Leads Extractor (Web Scraper)

Uma ferramenta automatizada em Python que usa o **Playwright** para simular um navegador invisível, buscar locais no Google Maps e extrair dados de estabelecimentos que **não possuem website**. 
Excelente para prospecção de clientes e geração de leads sem custos de API.

## Requisitos
- Python 3.8+
- Playwright (Navegador Chromium)

## Configuração
1. Abra um terminal na pasta do projeto.
2. Crie um ambiente virtual e ative-o:
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate 
   # No Linux/Mac:
   # source venv/bin/activate 
   ```
3. Instale as dependências. O segundo comando irá baixar a engine do navegador Chromium que o script usará para navegar invisivelmente.
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

## Como Usar
Execute o script `main.py` passando o termo de busca **exatamente como você digitaria no Google Maps**.

```bash
python main.py "Clínicas odontológicas na Vila Mariana, São Paulo"
```

### Argumentos Opcionais:
- `--max`: Define o número máximo de empresas que o robô tentará carregar e raspar na barra lateral do maps (Padrão: 50). Dependendo do termo, o Google Maps só carrega até 120 resultados de uma vez.
  
  Exemplo limitando a busca aos 20 primeiros:
  ```bash
  python main.py "Clínicas odontológicas na Vila Mariana, São Paulo" --max 20
  ```

## Banco de Dados
Os dados extraídos (empresas que **não** possuem site) são automaticamente salvos em um banco de dados local chamado `leads.db` (criado automaticamente na raiz do projeto, usando SQLite). 

A aplicação lida automaticamente com possíveis repetições e ignora empresas que você já extraiu antes.
Para visualizar e exportar a tabela para Excel ou CSV, baixe um software gratuito como o **DB Browser for SQLite** ou extensões do VSCode.

## Limitações do Web Scraper
Como a varredura simula um ser humano:
- O processo demora alguns minutos pois ele precisa aguardar o carregamento e rolagem da página.
- Se exigido muita velocidade, o Google Maps pode exibir um "Captcha". O script utiliza pausas para minimizar esse risco.
- Mudanças no layout do Google Maps podem quebrar regras de raspagem no futuro.
