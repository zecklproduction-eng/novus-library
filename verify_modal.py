import requests

try:
    s = requests.Session()
    # Login
    s.post('http://127.0.0.1:5000/login', data={'username':'admin', 'password':'123'})
    
    # Check Add Book
    r = s.get('http://127.0.0.1:5000/add')
    print(f"Debug: Status {r.status_code}, URL {r.url}")
    # print(f"Debug Content Snippet: {r.text[:500]}")
    
    has_buttons = 'Manage Transcript' in r.text and 'Manage Summary & TOC' in r.text
    has_modals = 'id="audioMetadataModal"' in r.text and 'id="structuredSummaryModal"' in r.text
    
    print(f"Add Book - Buttons Present: {has_buttons}")
    print(f"Add Book - Modals Present: {has_modals}")
    
    if not has_buttons or not has_modals:
        print("FAIL: Add Book page missing components.")
    
    # Check Edit Book (need a book ID, assuming 9 exists from previous context or generic check)
    # Just checking template structure if possible, but edit requires ID.
    # Let's try grabbing a book ID from home page if needed, or just hardcode 9.
    r2 = s.get('http://127.0.0.1:5000/book/9/edit')
    if r2.status_code == 200:
        if 'data-bs-target="#audioMetadataModal"' in r2.text and 'data-bs-target="#structuredSummaryModal"' in r2.text:
            print(f"Edit Book - Both Modals Trigger Buttons Present: True")
        else:
            print(f"Edit Book - Modals Trigger Buttons Missing")

        if 'id="audioMetadataModal"' in r2.text and 'id="structuredSummaryModal"' in r2.text:
            print(f"Edit Book - Both Modals Content Present: True")
        else:
            print(f"Edit Book - Modals Content Missing")
            
        if 'Manage Transcript' in r2.text and 'Manage Summary & TOC' in r2.text:
             print(f"PASS: New Button Labels found")
        else:
             print(f"FAIL: New Button Labels NOT found")

        if 'name="custom_summary"' in r2.text:
            print(f"PASS: Custom summary field found on {r2.url}")
        else:
             print(f"FAIL: Custom summary field NOT found on {r2.url}")
        
        if 'name="toc"' in r2.text:
            print(f"PASS: TOC field found on {r2.url}")
        else:
             print(f"FAIL: TOC field NOT found on {r2.url}")
    else:
        print(f"Edit Book - Failed to load (Status {r2.status_code})")

    # Check Book Detail Page (view_book)
    r3 = s.get('http://127.0.0.1:5000/book/9')
    if r3.status_code == 200:
        print(f"PASS: Book Detail page loaded successfully ({r3.url})")
        if "<title>" in r3.text and "NOVUS" in r3.text:
             print("PASS: Title tag appears correct.")
    else:
        print(f"FAIL: Book Detail page failed to load (Status {r3.status_code})")

    # Check Read Book Page
    r4 = s.get('http://127.0.0.1:5000/read/9')
    if r4.url == 'http://127.0.0.1:5000/':
         print(f"FAIL: Read Book Redirected to Home. Checking for error message...")
         if "An unexpected error occurred" in r4.text:
             print("FOUND ERROR MSG in HTML response.")
             for line in r4.text.split('\n'):
                 if "An unexpected error occurred" in line:
                     print(f"ERROR DETAIL: {line.strip()}")
    elif r4.status_code == 200:
        print(f"PASS: Read Book page loaded successfully ({r4.url})")
    else:
        print(f"FAIL: Read Book page failed (Status {r4.status_code})")

except Exception as e:
    print(f"Error: {e}")
