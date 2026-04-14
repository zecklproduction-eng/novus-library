import os

filename = r'd:\nist project\computer\library\novus-library\templates\group.html'
with open(filename, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = 0
for i, line in enumerate(lines):
    if skip > 0:
        skip -= 1
        continue
    
    # Match the broken block exactly
    if "const currentUserId = window.currentUserId || {{ session.get('user_id', 0)" in line and "}}" not in line:
        print(f"Fixing broken block starting at line {i+1}")
        # Next lines should be the closures
        if i + 2 < len(lines) and "}" in lines[i+1] and "};" in lines[i+2]:
            new_lines.append(line.replace("{{ session.get('user_id', 0)", "{{ session.get('user_id', 0) }};\n"))
            new_lines.append("\n") # Add blank line for spacing as in my previous attempt
            skip = 2
        else:
            # Just fix the line if closures don't match exactly
            new_lines.append(line.replace("{{ session.get('user_id', 0)", "{{ session.get('user_id', 0) }};\n"))
    else:
        new_lines.append(line)

with open(filename, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Done.")
