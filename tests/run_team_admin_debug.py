from app import app

def run():
    client = app.test_client()
    # login as admin
    client.post('/login', data={'username': 'admin', 'password': '123'})
    r = client.get('/admin/team')
    print('status', r.status_code)
    print(r.get_data(as_text=True)[:1000])

if __name__ == '__main__':
    run()
