from app import app, get_conn
from datetime import datetime, timedelta
import os


def test_admin_access_control():
    client = app.test_client()
    # not logged in -> redirected
    r = client.get('/admin/ai_summaries')
    assert r.status_code in (302, 301)


def test_admin_list_and_clear_actions():
    client = app.test_client()
    # login as admin
    client.post('/login', data={'username': 'admin', 'password': '123'})

    conn = get_conn()
    c = conn.cursor()

    # Insert a recent entry
    now = datetime.utcnow().isoformat()
    c.execute("INSERT INTO ai_summaries (item_type, item_id, summary, model, created_at) VALUES (?, ?, ?, ?, ?)",
              ('book', 9999, 'recent summary', 'simple', now))
    conn.commit()
    # get its id
    c.execute("SELECT id FROM ai_summaries WHERE item_type=? AND item_id=?", ('book', 9999))
    recent = c.fetchone()[0]

    # Insert an old entry (3 days ago)
    old_dt = (datetime.utcnow() - timedelta(days=3)).isoformat()
    c.execute("INSERT INTO ai_summaries (item_type, item_id, summary, model, created_at) VALUES (?, ?, ?, ?, ?)",
              ('book', 8888, 'old summary', 'simple', old_dt))
    conn.commit()
    c.execute("SELECT id FROM ai_summaries WHERE item_type=? AND item_id=?", ('book', 8888))
    old_id = c.fetchone()[0]

    conn.close()

    # GET page
    r = client.get('/admin/ai_summaries')
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert 'AI Summaries Cache' in html
    assert str(recent) in html
    assert str(old_id) in html

    # Clear selected (recent)
    r2 = client.post('/admin/ai_summaries/clear', json={'action': 'selected', 'ids': [recent]})
    assert r2.status_code == 200
    data = r2.get_json()
    assert data.get('deleted', 0) == 1

    # Ensure it is removed
    conn = get_conn(); c = conn.cursor()
    c.execute('SELECT id FROM ai_summaries WHERE id=?', (recent,)); assert c.fetchone() is None

    # Set TTL to 1 day to clear old entry
    os.environ['AI_SUMMARY_TTL_DAYS'] = '1'
    r3 = client.post('/admin/ai_summaries/clear', json={'action': 'expired'})
    assert r3.status_code == 200
    data2 = r3.get_json()
    # old entry should be deleted
    assert data2.get('deleted', 0) >= 1
    conn.close()


    def test_admin_fix_uploaders():
        client = app.test_client()
        client.post('/login', data={'username': 'admin', 'password': '123'})
        # create a book with no uploader
        conn = get_conn(); c = conn.cursor()
        c.execute("INSERT INTO books (title, author, category) VALUES (?, ?, ?)", ('No Uploader', 'Anon', 'General'))
        conn.commit()
        c.execute("SELECT id FROM books WHERE title=? ORDER BY id DESC", ('No Uploader',))
        bid = c.fetchone()[0]
        conn.close()

        # POST assign to current admin
        r = client.post('/admin/fix_uploaders', json={'ids': [bid]})
        assert r.status_code == 200
        data = r.get_json()
        assert data.get('updated', 0) >= 1

        # verify
        conn = get_conn(); c = conn.cursor()
        c.execute('SELECT uploader_id FROM books WHERE id=?', (bid,))
        row = c.fetchone(); conn.close()
        assert row and row[0] is not None
