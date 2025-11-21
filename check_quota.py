import sqlite3
from datetime import datetime, timedelta

def count_recent_tweets():
    conn = sqlite3.connect('tweets.db')
    cursor = conn.cursor()
    
    # Calculer la date d'hier à la même heure
    yesterday = datetime.now() - timedelta(days=1)
    
    cursor.execute('''
        SELECT COUNT(*) 
        FROM tweets 
        WHERE status = 'sent' 
        AND created_at >= ?
    ''', (yesterday,))
    
    count = cursor.fetchone()[0]
    
    print(f"Tweets envoyés ces dernières 24h : {count}")
    
    # Détails
    cursor.execute('''
        SELECT created_at, content 
        FROM tweets 
        WHERE status = 'sent' 
        AND created_at >= ?
        ORDER BY created_at DESC
    ''', (yesterday,))
    
    tweets = cursor.fetchall()
    if tweets:
        print("\nDétails :")
        for t in tweets:
            print(f"- {t[0]} : {t[1][:50]}...")
            
    conn.close()

if __name__ == "__main__":
    count_recent_tweets()
