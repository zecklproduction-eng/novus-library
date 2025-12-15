from app import app, get_conn


def test_edit_book_categories_and_description():
    client = app.test_client()
    # login as admin
    client.post('/login', data={'username': 'admin', 'password': '123'})

    # create a temporary book
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO books (title, author, category, description) VALUES (?, ?, ?, ?)",
              ('Test Edit Book', 'Tester', 'General', 'Initial description'))
    conn.commit()
    book_id = c.lastrowid
    conn.close()

    # GET edit form
    r = client.get(f'/book/{book_id}/edit')
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert 'Categories' in html
    assert 'Description' in html

    # POST updated categories and description
    # post categories as repeated form fields
    data = [
        ('categories', 'Fantasy'),
        ('categories', 'Adventure'),
        ('description', 'Updated description for testing.'),
        ('title', 'Test Edit Book'),
    ]
    r2 = client.post(f'/book/{book_id}/edit', data=data)
    # Should redirect to view
    assert r2.status_code in (302, 301)

    # Verify changes in DB
    conn = get_conn(); c = conn.cursor()
    c.execute('SELECT category, description FROM books WHERE id=?', (book_id,))
    row = c.fetchone()
    conn.close()
    assert row is not None
    category, description = row
    assert 'Fantasy' in category and 'Adventure' in category
    assert description == 'Updated description for testing.'


def test_add_book_sets_uploader():
    client = app.test_client()
    client.post('/login', data={'username': 'admin', 'password': '123'})
    # add a minimal book
    data = {
        'title': 'Uploader Test',
        'author': 'Tester',
        'book_type': 'book'
    }
    r = client.post('/add', data=data)
    assert r.status_code in (302, 301)
    # find book
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id, uploader_id FROM books WHERE title=? ORDER BY id DESC", ('Uploader Test',))
    row = c.fetchone()
    conn.close()
    assert row is not None
    assert row[1] is not None, 'uploader_id should be set when adding a book'
