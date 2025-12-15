from app import app
import re

client = app.test_client()
resp = client.get('/manga')
print('/manga ->', resp.status_code)
html = resp.get_data(as_text=True)
m = re.search(r"/manga/read/(\d+)", html)
print('found manga link?', bool(m))
if m:
    manga_id = m.group(1)
    # try accessing read page without login
    r2 = client.get(f'/manga/read/{manga_id}')
    print(f'/manga/read/{manga_id} without login ->', r2.status_code)
    print('Headers:', r2.headers)
    # now login
    login = client.post('/login', data={'username':'admin','password':'123'})
    print('/login ->', login.status_code)
    r3 = client.get(f'/manga/read/{manga_id}')
    print(f'/manga/read/{manga_id} after login ->', r3.status_code)
    print('Length of page:', len(r3.get_data(as_text=True)))
