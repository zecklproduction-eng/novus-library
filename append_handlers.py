
import os

app_path = r"d:\nist project\computer\library\novus-library\app.py"

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the specific missing except block at the end if it's missing
expected_end_fragment = """        return jsonify({
            'success': True,
            'extracted_text': text
        })"""

if expected_end_fragment in content and "text extraction failed" not in content[-500:]:
    print("Repairing missing except block...")
    # Find the last occurrence and append the except block
    parts = content.rsplit(expected_end_fragment, 1)
    if len(parts) == 2:
        content = parts[0] + expected_end_fragment + """
    
    except Exception as e:
        return jsonify({'error': f'Text extraction failed: {str(e)}'}), 500
"""

# Append error handlers if not present
handlers_code = """

# Global Error Handlers for API JSON responses
@app.errorhandler(413)
def request_entity_too_large(error):
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": f"File too large. Max size is {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB"}), 413
    return "File too large", 413

@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": "Resource not found"}), 404
    return "Not Found", 404

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": "Internal server error"}), 500
    return "Internal Server Error", 500
"""

if "@app.errorhandler(413)" not in content:
    print("Appending error handlers...")
    content += handlers_code
else:
    print("Error handlers already present.")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done.")
