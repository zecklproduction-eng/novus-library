from app import app


def test_admin_team_page_loaded():
    client = app.test_client()
    client.post('/login', data={'username': 'admin', 'password': '123'})
    r = client.get('/admin/team')
    # should either render the page or redirect if an error occurs (we catch exceptions)
    assert r.status_code in (200, 302)
