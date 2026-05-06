import random

class MessageGenerator:
    """
    Classe responsável por gerar mensagens personalizadas para prospecção via WhatsApp.
    O objetivo principal é variar as saudações para evitar bloqueios por spam,
    e injetar os dados da empresa (nome, link demo) no modelo certo.
    """
    
    @staticmethod
    def get_greeting():
        """Retorna uma saudação aleatória para dar sensação de mensagem humana."""
        greetings = [
            "Olá, tudo bem?",
            "Oi, tudo bem?",
            "Olá, como vai?",
            "Oi! Tudo certo?",
            "Olá! Tudo bem com vocês?"
        ]
        return random.choice(greetings)
        
    @staticmethod
    def clean_company_name(name):
        """Limpa o nome da empresa, ex: removendo 'Ltda', 'ME', para ficar mais natural."""
        remove_terms = [' ltda', ' me', ' eireli', ' s.a.', ' s/a', ' epp']
        name_lower = name.lower()
        
        # Só remove se estiver no final da string 
        for term in remove_terms:
            if name_lower.endswith(term):
                name = name[:-len(term)].strip()
                name_lower = name.lower()
                
        # Tenta capitalizar de forma amigável
        return name.title()

    @classmethod
    def generate_first_contact_no_website(cls, company_name):
        """
        Gera a mensagem para empresas que NÃO possuem site.
        """
        greeting = cls.get_greeting()
        name = cls.clean_company_name(company_name)
        
        message = (
            f"{greeting}\n\n"
            f"Estava pesquisando empresas da região e encontrei a {name}.\n\n"
            "Percebi que ainda não há um site institucional ativo, então preparei um modelo "
            "demonstrativo inicial mostrando como poderia ficar um site profissional para vocês.\n\n"
            "Posso te enviar o link para você dar uma olhada?"
        )
        return message

    @classmethod
    def generate_first_contact_with_website(cls, company_name):
        """
        Gera a mensagem para empresas que JÁ possuem site, mas que pode ser melhorado.
        """
        greeting = cls.get_greeting()
        name = cls.clean_company_name(company_name)
        
        message = (
            f"{greeting}\n\n"
            f"Estava analisando o site da {name} e identifiquei alguns pontos que podem "
            "melhorar bastante a presença digital e a conversão de clientes.\n\n"
            "Preparei um modelo demonstrativo com melhorias para mostrar o potencial de atualização.\n\n"
            "Posso te enviar para você avaliar?"
        )
        return message

