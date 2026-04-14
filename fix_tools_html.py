
import os

file_path = r'd:\nist project\computer\library\novus-library\templates\tools.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Look for the problematic lines around 1362 (0-indexed 1361)
modified = False
for i in range(len(lines)):
    if "const isAdmin = {{ 'true' if is_admin else 'false' }" in lines[i] and i + 1 < len(lines) and "};" in lines[i+1]:
        print(f"Found problematic code at index {i}")
        lines[i] = "        const isAdmin = {{ 'true' if is_admin else 'false' }};\n"
        # We want to remove the next line '    };'
        # But wait, does the next line have other stuff? 
        # In view_file it was just '    };'
        if lines[i+1].strip() == "};":
            lines[i+1] = "" # Clear it
            modified = True
            print("Fixed line and cleared next line.")
        break

if modified:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines([l for l in lines if l]) # Filter out empty lines if any
    print("File updated successfully.")
else:
    print("Could not find the problematic pattern.")
