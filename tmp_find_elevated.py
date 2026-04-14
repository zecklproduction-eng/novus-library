import re
with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

matches = re.finditer(r'@elevated_required\s*\n\s*def\s+([a-zA-Z0-9_]+)', content)
for m in matches:
    print(m.group(1))
