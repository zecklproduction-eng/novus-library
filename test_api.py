from app import app, init_db, get_conn
import json
import unittest
import re

class TestCommunityReviewsAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        init_db()
        
        # Ensure a test user exists
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                  ("testuser", "test@test.com", "password", "reader"))
        conn.commit()
        # Get user id
        c.execute("SELECT id FROM users WHERE username='testuser'")
        self.user_id = c.fetchone()[0]
        
        # Ensure a book exists
        c.execute("INSERT OR IGNORE INTO books (title, author, category, book_type) VALUES (?, ?, ?, ?)", 
                  ('Test API Book', 'Test Author', 'Education', 'book'))
        conn.commit()
        conn.close()

    def login(self):
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.user_id
            sess['username'] = 'testuser'
            sess['role'] = 'reader'

    def test_media_search(self):
        response = self.app.get('/api/media/search?q=Test API')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0]['title'], 'Test API Book')
        # Check cover URL format
        cover_url = data[0]['coverUrl']
        self.assertTrue(cover_url.startswith('/static/') or cover_url.startswith('http'))

    def test_post_review_flow(self):
        self.login()
        
        # 1. Post Review
        payload = {
            "title": "Test API Book",
            "rating": 5,
            "body": "This is a test review via API.",
            "hasSpoilers": False,
            "status": "Completed"
        }
        response = self.app.post('/api/reviews/post', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # 2. Verify it exists in DB
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, content FROM reviews WHERE content=?", (payload['body'],))
        review = c.fetchone()
        self.assertIsNotNone(review)
        review_id = review[0]
        conn.close()
        
        # 3. Like Review
        response = self.app.post('/api/reviews/like',
                                 data=json.dumps({"reviewId": review_id}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['action'], 'liked')
        
        # 4. Unlike Review
        response = self.app.post('/api/reviews/like',
                                 data=json.dumps({"reviewId": review_id}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['action'], 'unliked')
        
        # 5. Comment on Review
        comment_payload = {
            "reviewId": review_id,
            "content": "Test comment API"
        }
        response = self.app.post('/api/reviews/comment',
                                 data=json.dumps(comment_payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # 6. Verify comment in DB
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT content FROM review_comments WHERE review_id=?", (review_id,))
        comment = c.fetchone()
        self.assertEqual(comment[0], "Test comment API")
        conn.close()

    def test_feed_cover_urls(self):
        self.login()
        # Post a review first to ensure there's data
        payload = {
            "title": "Test API Book",
            "rating": 5,
            "body": "Cover URL Test Review",
            "hasSpoilers": False,
            "status": "Completed"
        }
        self.app.post('/api/reviews/post', data=json.dumps(payload), content_type='application/json')
        
        response = self.app.get('/community/reviews')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        
        # Look for the initial_reviews data injection
        match = re.search(r'const INITIAL_REVIEWS = (\[.*?\]);', content, re.DOTALL)
        if match:
            reviews_json = match.group(1)
            # Simplistic check for /static/ or http in the JSON string for coverUrl
            # We assume the seeded/posted book has a cover that will be processed
            self.assertTrue('/static/' in reviews_json or 'http' in reviews_json)

    def test_comment_like(self):
        self.login()
        # 1. Post a review
        payload = { "title": "Test API Book", "rating": 5, "body": "Review for comment like", "hasSpoilers": False, "status": "Reading" }
        response = self.app.post('/api/reviews/post', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200, f"Post failed: {response.data}")
        
        # Get review ID
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id FROM reviews WHERE content = 'Review for comment like'")
        review_id = c.fetchone()[0]
        conn.close()
        
        # 2. Post a comment
        self.app.post('/api/reviews/comment', 
                      data=json.dumps({"reviewId": review_id, "content": "Like me!"}), 
                      content_type='application/json')
                      
        # Get comment ID
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id FROM review_comments WHERE content = 'Like me!'")
        comment_id = c.fetchone()[0]
        conn.close()
        
        # 3. Like the comment
        response = self.app.post('/api/reviews/comments/like',
                                 data=json.dumps({"commentId": comment_id}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['action'], 'liked')
        
        # Verify DB
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM comment_likes WHERE comment_id = ?", (comment_id,))
        self.assertEqual(c.fetchone()[0], 1)
        conn.close()
        
        # 4. Unlike the comment
        response = self.app.post('/api/reviews/comments/like',
                                 data=json.dumps({"commentId": comment_id}),
                                 content_type='application/json')
        self.assertEqual(response.json['action'], 'unliked')
        
        # Verify DB
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM comment_likes WHERE comment_id = ?", (comment_id,))
        self.assertEqual(c.fetchone()[0], 0)
        conn.close()

    def test_update_review(self):
        self.login()
        # 1. Post a review
        payload = { "title": "Test API Book", "rating": 5, "body": "Original Review Body", "hasSpoilers": False, "status": "Reading" }
        self.app.post('/api/reviews/post', data=json.dumps(payload), content_type='application/json')
        
        # Get review ID
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id FROM reviews WHERE content = 'Original Review Body'")
        review_id = c.fetchone()[0]
        conn.close()
        
        # 2. Update the review
        update_payload = {
            "reviewId": review_id,
            "rating": 4,
            "body": "Updated Review Body",
            "hasSpoilers": True,
            "status": "Completed"
        }
        response = self.app.post('/api/reviews/update', data=json.dumps(update_payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])
        
        # 3. Verify DB update
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT rating, content, has_spoilers, status FROM reviews WHERE id = ?", (review_id,))
        row = c.fetchone()
        self.assertEqual(row[0], 4)
        self.assertEqual(row[1], "Updated Review Body")
        self.assertEqual(row[2], 1) # Boolean True is 1 in SQLite
        self.assertEqual(row[3], "Completed")
        conn.close()

        # 4. Try to update someone else's review
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, role) VALUES ('otheruser', 'pass', 'reader')")
        other_user_id = c.lastrowid
        c.execute("INSERT INTO reviews (user_id, book_id, content, rating, has_spoilers) VALUES (?, ?, 'Other review', 3, 0)",
                 (other_user_id, 1)) # Assuming book_id 1 is the book
        other_review_id = c.lastrowid
        conn.commit()
        conn.close()
        
        fail_payload = update_payload.copy()
        fail_payload['reviewId'] = other_review_id
        response = self.app.post('/api/reviews/update', data=json.dumps(fail_payload), content_type='application/json')
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()
