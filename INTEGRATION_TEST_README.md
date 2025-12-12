# Integration Test Guide

## Running the Integration Test

The integration test in `tests/test_flow.py` validates core workflows:
- User registration (Publisher account)
- Access to upload page (`/add`)
- Book upload with PDF and cover image
- Watchlist add, update, and remove operations

### Prerequisites

Ensure Flask is running in debug mode (or in a separate terminal):

```bash
python app.py
```

### Running the Test

In another terminal, run:

```bash
python tests/test_flow.py
```

### Expected Output

```
Registering user testpub_<timestamp>
Register status 200
/add GET 200
Uploading book...
/add POST 200
Uploaded book id <N>
watchlist add response 200
watchlist update response 200
watchlist remove response 200
Test flow complete
```

### What It Tests

1. **Registration**: Creates a Publisher account via `/register`
2. **Upload Access**: Verifies `/add` page is accessible to Publishers
3. **Book Upload**: Posts PDF + cover image to `/add`, confirms DB insert
4. **Watchlist Add**: Adds the uploaded book to watchlist via `/watchlist/book/<id>`
5. **Watchlist Update**: Updates status and progress via `/watchlist/update`
6. **Watchlist Remove**: Removes the book via `/watchlist/remove`

### Cleanup

Test uploads are stored in `tests/tmp/`. The test script does not delete uploaded books from the database — you can manually clean them up using the admin dashboard or by querying the database directly.

### Troubleshooting

- **Connection refused**: Ensure Flask is running on `http://127.0.0.1:5000`
- **Database locked**: Close any other database connections and restart Flask
- **Uploaded book not found**: Check `library.db` to verify the book was inserted

