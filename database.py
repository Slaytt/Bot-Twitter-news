import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_NAME = "tweets.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise la base de données avec la table tweets."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tweets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        scheduled_time TIMESTAMP NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', -- pending, sent, failed, skipped
        twitter_id TEXT,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monitored_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        interval_minutes INTEGER DEFAULT 60,
        last_run TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processed_urls (
        url TEXT PRIMARY KEY,
        topic_id INTEGER,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(topic_id) REFERENCES monitored_topics(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_scheduled_tweet(content: str, run_date: datetime) -> int:
    """Ajoute un tweet à la file d'attente."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO tweets (content, scheduled_time, status) VALUES (?, ?, ?)',
        (content, run_date, 'pending')
    )
    
    tweet_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tweet_id

def get_pending_tweets() -> List[Dict]:
    """Récupère les tweets en attente dont l'heure est passée (pour le scheduler)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    
    cursor.execute(
        'SELECT * FROM tweets WHERE status = ? AND scheduled_time <= ?',
        ('pending', now)
    )
    
    tweets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tweets

def get_all_pending_tweets() -> List[Dict]:
    """Récupère TOUS les tweets en attente (pour l'interface)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT * FROM tweets WHERE status = ? ORDER BY scheduled_time ASC',
        ('pending',)
    )
    
    tweets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tweets

def delete_scheduled_tweet(tweet_id: int):
    """Supprime un tweet programmé."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM tweets WHERE id = ?', (tweet_id,))
    
    conn.commit()
    conn.close()

def update_tweet_status(tweet_id: int, status: str, twitter_id: Optional[str] = None, error: Optional[str] = None):
    """Met à jour le statut d'un tweet."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        '''
        UPDATE tweets 
        SET status = ?, twitter_id = ?, error_message = ? 
        WHERE id = ?
        ''',
        (status, twitter_id, error, tweet_id)
    )
    
    conn.commit()
    conn.close()

def get_monthly_count() -> int:
    """Compte le nombre de tweets envoyés ce mois-ci."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    cursor.execute(
        '''
        SELECT COUNT(*) as count 
        FROM tweets 
        WHERE status = 'sent' 
        AND scheduled_time >= ?
        ''',
        (start_of_month,)
    )
    
    result = cursor.fetchone()
    conn.close()
    return result['count'] if result else 0

# --- Monitoring Functions ---

def add_monitored_topic(query: str, interval_minutes: int = 60) -> int:
    """Ajoute un sujet à surveiller."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO monitored_topics (query, interval_minutes) VALUES (?, ?)',
        (query, interval_minutes)
    )
    
    topic_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return topic_id

def get_active_topics() -> List[Dict]:
    """Récupère les sujets actifs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM monitored_topics WHERE is_active = 1')
    
    topics = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return topics

def update_topic_last_run(topic_id: int):
    """Met à jour la date de dernière exécution d'un sujet."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE monitored_topics SET last_run = ? WHERE id = ?',
        (datetime.now(), topic_id)
    )
    
    conn.commit()
    conn.close()

def is_url_processed(url: str) -> bool:
    """Vérifie si une URL a déjà été traitée."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT 1 FROM processed_urls WHERE url = ?', (url,))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None

def mark_url_processed(url: str, topic_id: int):
    """Marque une URL comme traitée."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO processed_urls (url, topic_id) VALUES (?, ?)',
            (url, topic_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Déjà existe
    finally:
        conn.close()

def delete_monitored_topic(topic_id: int):
    """Supprime (désactive) un sujet."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE monitored_topics SET is_active = 0 WHERE id = ?', (topic_id,))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Test rapide si exécuté directement
    init_db()
    print("Database initialized.")
