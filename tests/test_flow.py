import requests
import time
import os
import sqlite3

BASE = 'http://127.0.0.1:5000'

s = requests.Session()

# Create test files
os.makedirs('tests/tmp', exist_ok=True)
with open('tests/tmp/sample.pdf','wb') as f:
    f.write(b'%PDF-1.4\n% Test PDF file\n')
with open('tests/tmp/cover.jpg','wb') as f:
    f.write(b'\xff\xd8\xff Test JPG')

username = f'testpub_{int(time.time())}'
email = username + '@example.test'
password = 'pw123'

print('Registering user', username)
r = s.post(BASE + '/register', data={
    'username': username,
    'email': email,
    'password': password,
    'confirm_password': password,
    'account_type': 'publisher'
}, allow_redirects=True)
print('Register status', r.status_code)

# Check we can access /add
r = s.get(BASE + '/add')
print('/add GET', r.status_code)

# Upload a book
print('Uploading book...')
with open('tests/tmp/sample.pdf','rb') as pdf, open('tests/tmp/cover.jpg','rb') as cover:
    files = {
        'pdf_file': ('sample.pdf', pdf, 'application/pdf'),
        'cover_image': ('cover.jpg', cover, 'image/jpeg')
    }
    data = {
        'title': 'Integration Test Book',
        'author': 'Test Author',
        'category': 'Test',
        'book_type': 'book'
    }
    r = s.post(BASE + '/add', data=data, files=files, allow_redirects=True)
    print('/add POST', r.status_code)

# Wait a beat for DB commit
time.sleep(0.5)

# Query DB for the uploaded book ID
conn = sqlite3.connect('library.db')
c = conn.cursor()
c.execute("SELECT id FROM books WHERE title=? ORDER BY id DESC LIMIT 1", ('Integration Test Book',))
row = c.fetchone()
if not row:
    print('Uploaded book not found in DB')
    raise SystemExit(1)
book_id = row[0]
print('Uploaded book id', book_id)

# Add to watchlist via book detail route endpoint
r = s.post(f'{BASE}/watchlist/book/{book_id}', data={'status':'planned'}, allow_redirects=True)
print('watchlist add response', r.status_code)

# Update watchlist entry
r = s.post(BASE + '/watchlist/update', data={'book_id': book_id, 'status': 'reading', 'progress': '30'}, allow_redirects=True)
print('watchlist update response', r.status_code)

# Remove watchlist entry
r = s.post(BASE + '/watchlist/remove', data={'book_id': book_id}, allow_redirects=True)
print('watchlist remove response', r.status_code)

print('Test flow complete')
