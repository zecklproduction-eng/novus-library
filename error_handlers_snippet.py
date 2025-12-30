@app.errorhandler(413)
def request_entity_too_large(error):
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": f"File too large. Max size is {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB"}), 413
    return "File too large", 413

@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": "Resource not found"}), 404
    return render_template("404.html"), 404 if os.path.exists(os.path.join(APP_ROOT, "templates", "404.html")) else ("Not Found", 404)

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": "Internal server error"}), 500
    return "Internal Server Error", 500
