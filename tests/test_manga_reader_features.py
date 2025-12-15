from app import app
import re


def test_ai_summary_endpoint():
    client = app.test_client()
    rv = client.post('/ai_summary', json={'text': 'This is a short description about a test manga. It is fun and exciting.', 'max_sentences': 2})
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'summary' in data and isinstance(data['summary'], str)
    assert len(data['summary'].strip()) > 0


def test_ai_summary_short_text_truncates():
    client = app.test_client()
    src = """This book follows a young hero through an intricately detailed fantasy world filled with political intrigue, magic academies, and fast-paced action that spans continents."""
    r = client.post('/ai_summary', json={'text': src, 'max_sentences': 1})
    assert r.status_code == 200
    d = r.get_json()
    # summary should not be identical to the original (should be concise)
    assert 'summary' in d
    assert d['summary'].strip() != src.strip()


def test_manga_reader_template_contains_ui_elements():
    client = app.test_client()
    # login first and get /manga to find a read link
    client.post('/login', data={'username': 'admin', 'password': '123'})
    r = client.get('/manga')
    assert r.status_code == 200
    m = re.search(r"/manga/read/(\d+)", r.get_data(as_text=True))
    assert m, 'No manga read links found'
    manga_id = m.group(1)

    # login first (test user 'admin' is present after init_db())
    client.post('/login', data={'username': 'admin', 'password': '123'})
    r2 = client.get(f'/manga/read/{manga_id}')
    assert r2.status_code == 200
    html = r2.get_data(as_text=True)
    assert 'id="mangaDescription"' in html
    assert 'id="mangaAiBtn"' in html
    assert 'id="progressSlider"' in html
    assert 'id="pageIndicator"' in html
    assert 'id="chapterSelect"' in html
    # new reader mode buttons
    assert 'Double Page' in html
    assert 'Vertical Scroll' in html
    assert 'Horizontal Scroll' in html
    # basic controls: fullscreen and zoom
    assert 'btnFullscreen' in html
    assert 'btnZoomIn' in html
    # thumbnails and pointer handlers present
    assert 'thumbnailStrip' in html
    assert 'pointerdown' in html or 'pointermove' in html
    # double page layout JS present
    assert 'pageContainer.style.display' in html
    assert 'double page' in html.lower() or 'double-page' in html.lower()
    # series reader: fullscreen and advanced settings present
    assert 'btnFullscreenSeries' in html
    assert 'Fit Width' in html
    assert 'Header Sticky' in html


def test_chapter_page_images_embedded():
    client = app.test_client()
    # login first
    client.post('/login', data={'username': 'admin', 'password': '123'})
    r = client.get('/manga')
    assert r.status_code == 200
    ids = re.findall(r"/manga/read/(\d+)", r.get_data(as_text=True))
    assert ids, 'No manga entries found'

    manga_id = None
    chapter_id = None
    # find first manga that has chapters
    for mid in ids:
        r2 = client.get(f'/manga/read/{mid}')
        cm = re.search(r"/manga/%s/chapter/(\d+)" % mid, r2.get_data(as_text=True))
        if cm:
            manga_id = mid
            chapter_id = cm.group(1)
            break

    assert manga_id and chapter_id, 'No manga with chapters found'
    chapter_id = cm.group(1)

    r3 = client.get(f'/manga/{manga_id}/chapter/{chapter_id}')
    assert r3.status_code == 200
    html = r3.get_data(as_text=True)
    assert 'id="pageContainer"' in html
    # ensure the chapter base folder string is present (manga_<id>_ch<chapter_num>)
    assert f"manga_{manga_id}_ch" in html
    # ensure new reading mode options are present on chapter viewer
    assert 'Double Page' in html
    assert 'Vertical Scroll' in html
    assert 'Horizontal Scroll' in html
    # ensure fullscreen/zoom buttons are present in chapter viewer
    assert 'btnFullscreen' in html
    assert 'btnZoomIn' in html
    # chapter viewer fit/direction options
    assert 'Fit Width' in html
    assert 'Left to Right' in html
    # auto-scroll and rotation controls
    assert 'Auto-Scroll' in html
    assert 'Rotation' in html
    # thumbnail hover preview string
    assert 'thumbHoverPreview' in html


def test_ai_summary_caching_for_book():
    client = app.test_client()
    # pick a book page
    client.post('/login', data={'username': 'admin', 'password': '123'})
    r = client.get('/book/4')
    assert r.status_code == 200
    # call ai_summary with item info
    payload = {'text': 'This is a test book description to cache.', 'max_sentences': 2, 'item_type': 'book', 'item_id': 4}
    r1 = client.post('/ai_summary', json=payload)
    assert r1.status_code == 200
    data1 = r1.get_json()
    assert 'summary' in data1
    # call again - should be cached
    r2 = client.post('/ai_summary', json=payload)
    assert r2.status_code == 200
    data2 = r2.get_json()
    assert data2.get('cached') is True
