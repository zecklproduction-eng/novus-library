import requests
import re


def test_manga_ai_summary():
    s = requests.Session()
    LOGIN_URL = 'http://127.0.0.1:5000/login'
    MANGA_URL = 'http://127.0.0.1:5000/manga'

    # login
    r = s.post(LOGIN_URL, data={'username': 'admin', 'password': '123'})
    assert r.status_code in (200, 302)

    # find a manga to read
    r = s.get(MANGA_URL)
    assert r.status_code == 200
    m = re.search(r"/manga/read/(\d+)", r.text)
    assert m, 'No manga read links found on /manga'
    manga_id = m.group(1)

    # load reader
    r = s.get(f'http://127.0.0.1:5000/manga/read/{manga_id}')
    assert r.status_code == 200
    mm = re.search(r'id="mangaDescription">([\s\S]*?)</p>', r.text)
    desc = mm.group(1).strip() if mm else ''

    # call ai_summary
    resp = s.post('http://127.0.0.1:5000/ai_summary', json={'text': desc, 'max_sentences': 3})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert 'summary' in data and isinstance(data['summary'], str)
    assert len(data['summary'].strip()) > 0

    print('AI summary:', data['summary'])
