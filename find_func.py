
filename = r"d:\nist project\computer\library\novus-library\app.py"
with open(filename, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "def request_monetization" in line:
            print(f"Found at line {i+1}: {line.strip()}")
