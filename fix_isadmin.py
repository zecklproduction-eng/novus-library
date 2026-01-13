import re

file_path = r'd:\nist project\computer\library\novus-library\templates\tools.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken isAdmin line
old_pattern = r"const isAdmin = \{\{ 'true' if is_admin else 'false' \}\s*\n\s*\};"
new_text = "const isAdmin = {{ 'true' if is_admin else 'false' }};"

content, count = re.subn(old_pattern, new_text, content)
print(f"Replaced {count} occurrences")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("File saved successfully!")

# Verify the fix
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[1370:1378], start=1371):
        print(f"{i}: {line.rstrip()}")
