import sqlite3
from datetime import datetime
import os

# Determina o caminho do banco de dados na raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'leads.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Criar tabela de leads se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            place_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            rating REAL,
            user_ratings_total INTEGER,
            opening_hours TEXT,
            category TEXT,
            search_radius REAL,
            google_maps_url TEXT,
            collected_at TIMESTAMP NOT NULL,
            contact_status TEXT DEFAULT 'not_contacted',
            interested BOOLEAN DEFAULT 0,
            last_contacted_at TIMESTAMP
        )
    ''')
    
    # Migrações para adicionar colunas em banco existente
    try:
        cursor.execute("ALTER TABLE leads ADD COLUMN contact_status TEXT DEFAULT 'not_contacted'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE leads ADD COLUMN interested BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE leads ADD COLUMN last_contacted_at TIMESTAMP")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def save_lead(lead_data):
    """
    Tenta salvar um lead no banco de dados.
    Retorna True se foi inserido, False se já existir ou der erro.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Prevenção extra: Não salvar se o telefone já existe em outro lead (Ex: Clínicas filiais)
        phone = lead_data.get('phone')
        if phone:
            cursor.execute('SELECT 1 FROM leads WHERE phone = ?', (phone,))
            if cursor.fetchone():
                return False
                
        cursor.execute('''
            INSERT INTO leads (
                place_id, name, address, phone, email, website, 
                rating, user_ratings_total, opening_hours, category, search_radius, google_maps_url, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lead_data.get('place_id'),
            lead_data.get('name'),
            lead_data.get('address'),
            lead_data.get('phone'),
            lead_data.get('email'),
            lead_data.get('website'),
            lead_data.get('rating'),
            lead_data.get('user_ratings_total'),
            lead_data.get('opening_hours'),
            lead_data.get('category'),
            lead_data.get('search_radius'),
            lead_data.get('google_maps_url'),
            datetime.now()
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # place_id já existe (duplicidade)
        return False
    finally:
        conn.close()

def get_lead_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM leads')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_leads_to_contact(limit=20):
    """Retorna leads que ainda não foram contatados e possuem telefone."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM leads 
        WHERE contact_status = 'not_contacted' AND phone IS NOT NULL
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_lead_status(place_id, status):
    """Atualiza o status de contato de um lead."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE leads 
        SET contact_status = ?, last_contacted_at = ?
        WHERE place_id = ?
    ''', (status, datetime.now(), place_id))
    conn.commit()
    conn.close()
