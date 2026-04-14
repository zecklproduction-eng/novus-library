import sys
import os

# Add relevant paths for importing app
sys.path.append(r'd:\nist project\computer\library\novus-library')

from app import app, get_conn
import json

def test_task_completion():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            # Assume user_id 1 is admin/valid user
            sess['user_id'] = 1
            sess['_permanent'] = True
        
        # 1. Complete task for the first time
        print("--- Testing first completion ---")
        response = client.post('/api/tasks/complete/write_review_1', headers={"X-Test-User-ID": "1"})
        print(f"Status Code: {response.status_code}")
        print(f"Data: {response.get_json()}")
        
        # 2. Complete again immediately (should fail due to 1-day cooldown)
        print("\n--- Testing cooldown enforcement ---")
        response = client.post('/api/tasks/complete/write_review_1', headers={"X-Test-User-ID": "1"})
        print(f"Status Code: {response.status_code}")
        print(f"Data: {response.get_json()}")
        
        # 3. Check coins in DB
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT coins FROM users WHERE id = 1")
        print(f"\nFinal Coins for user 1: {c.fetchone()[0]}")
        conn.close()

if __name__ == "__main__":
    test_task_completion()
