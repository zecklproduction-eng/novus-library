file_path = r'd:\nist project\computer\library\novus-library\templates\avatar_studio.html'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "session.get('username')" in line:
        print(f"Line {i+1}: {line.strip()}")
