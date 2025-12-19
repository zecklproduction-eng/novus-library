import pytest
from app import app, init_db, get_conn


@pytest.fixture(autouse=True)
def prepare_db(tmp_path):
    # ensure DB exists and has defaults
    init_db()
    yield


def test_admin_sets_ultimate_plan():
    client = app.test_client()

    # login as admin (seeded by init_db)
    resp = client.post('/login', data={'username': 'admin', 'password': '123'}, follow_redirects=True)
    assert resp.status_code in (200, 302)

    # find a non-admin user
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", ('student',))
    row = c.fetchone()
    assert row is not None
    user_id = row[0]
    conn.close()

    # set plan to ultimate
    resp = client.post(f'/admin/users/{user_id}/plan', data={'plan': 'ultimate'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Plan updated to ultimate' in resp.data

    # confirm in DB
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT plan, plan_expires_at FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    assert row[0] == 'ultimate'
    assert row[1] is None
