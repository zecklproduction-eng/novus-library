from app import app
import logging

# Capture log output
logging.basicConfig(level=logging.ERROR)

print("Starting reproduction script...")
try:
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'admin'
        
        print("Making request to /manga ...")
        response = client.get('/manga')
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 500:
            print("Captured 500 error.")
            # The server log helper I added should have printed the traceback to stderr already.
            # But just in case, print response text if it contains the error
            print(response.get_data(as_text=True))
        elif response.status_code == 302:
            print("Redirected to:", response.headers.get('Location'))
        else:
             print("Success.")

except Exception as e:
    import traceback
    traceback.print_exc()
