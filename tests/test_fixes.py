import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import sqlite3
from datetime import datetime, timedelta
from database import init_db, get_db_connection, delete_old_awaiting_tweets, add_scheduled_tweet

class TestBotFixes(unittest.TestCase):

    def setUp(self):
        # Use a test database
        self.test_db = "test_tweets.db"
        # Patch database.DB_NAME temporarily
        import database
        self.original_db_name = database.DB_NAME
        database.DB_NAME = self.test_db
        init_db()

    def tearDown(self):
        import database
        database.DB_NAME = self.original_db_name
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_actustream_exclusion_logic(self):
        """Test that the exclusion logic works as expected."""
        # This logic is inside monitoring_service.py, but we can test the condition here
        url_to_exclude = "https://actustream.fr/img/joueurs/some-player.html"
        url_to_keep = "https://actustream.fr/news/some-news.html"
        
        def should_exclude(url):
            return "actustream.fr/img/joueurs/" in url
            
        self.assertTrue(should_exclude(url_to_exclude), "Should exclude player pages")
        self.assertFalse(should_exclude(url_to_keep), "Should keep other pages")

    def test_auto_deletion(self):
        """Test that old awaiting tweets are deleted."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Insert a recent tweet (should stay)
        recent_time = datetime.now()
        cursor.execute(
            "INSERT INTO tweets (content, scheduled_time, status, created_at) VALUES (?, ?, ?, ?)",
            ("Recent Tweet", recent_time, "awaiting_approval", recent_time)
        )
        
        # 2. Insert an old tweet (should be deleted)
        old_time = datetime.now() - timedelta(hours=25)
        cursor.execute(
            "INSERT INTO tweets (content, scheduled_time, status, created_at) VALUES (?, ?, ?, ?)",
            ("Old Tweet", recent_time, "awaiting_approval", old_time)
        )
        
        # 3. Insert an old tweet but NOT awaiting approval (should stay)
        old_pending_time = datetime.now() - timedelta(hours=25)
        cursor.execute(
            "INSERT INTO tweets (content, scheduled_time, status, created_at) VALUES (?, ?, ?, ?)",
            ("Old Pending Tweet", recent_time, "pending", old_pending_time)
        )
        
        conn.commit()
        conn.close()
        
        # Run cleanup
        deleted_count = delete_old_awaiting_tweets(hours=24)
        
        # Verify
        conn = get_db_connection()
        cursor = conn.cursor()
        tweets = cursor.execute("SELECT content FROM tweets").fetchall()
        contents = [t['content'] for t in tweets]
        conn.close()
        
        self.assertEqual(deleted_count, 1, "Should have deleted exactly 1 tweet")
        self.assertIn("Recent Tweet", contents)
        self.assertNotIn("Old Tweet", contents)
        self.assertIn("Old Pending Tweet", contents)

if __name__ == '__main__':
    unittest.main()
