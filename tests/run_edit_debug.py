from app import app, get_conn


def run():
    client = app.test_client()
    # login as admin
    client.post('/login', data={'username': 'admin', 'password': '123'})

    # find an existing book id
    conn = get_conn(); c = conn.cursor()
    c.execute('SELECT id FROM books LIMIT 1')
    row = c.fetchone()
    conn.close()
    if not row:
        print('No books found in DB')
        return
    book_id = row[0]

    print('Testing GET /book/{}/edit'.format(book_id))
    r = client.get(f'/book/{book_id}/edit')
    print('GET status:', r.status_code)
    print(r.get_data(as_text=True)[:1000])

    print('\nTesting POST /book/{}/edit'.format(book_id))
    payload = {'title': 'Edited Title Debug', 'author': 'Debug', 'categories': ['Fantasy', 'Romance'], 'description': 'Edited in debug'}
    r2 = client.post(f'/book/{book_id}/edit', data=payload)
    print('POST status:', r2.status_code)
    print(r2.get_data(as_text=True)[:500])


if __name__ == '__main__':
    run()
