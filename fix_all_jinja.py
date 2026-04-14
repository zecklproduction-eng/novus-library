
import os
import re

FILE_PATH = r'd:\nist project\computer\library\novus-library\templates\group.html'

def fix_all():
    if not os.path.exists(FILE_PATH):
        print("File not found.")
        return

    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all instances of the broken pattern
    # Pattern: {{ session.get('user_id', 0) followed by newline and }
    broken_pattern = re.compile(
        r"\{\{ session\.get\('user_id', 0\)\s*\n\s*\}\s*\n\s*\};"
    )
    
    matches = list(broken_pattern.finditer(content))
    print(f"Found {len(matches)} occurrences of broken pattern")
    
    for match in matches:
        start = max(0, match.start() - 50)
        end = min(len(content), match.end() + 50)
        print(f"Match at position {match.start()}: ...{content[start:end]}...")
    
    # Replace all occurrences
    fixed_content = broken_pattern.sub(
        "{{ session.get('user_id', 0) }};",
        content
    )
    
    if fixed_content != content:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"Fixed {len(matches)} occurrences.")
    else:
        print("No matches found with regex. Trying line-by-line approach...")
        
        lines = content.splitlines()
        fixed_lines = []
        i = 0
        fixes = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line ends with {{ session.get('user_id', 0)
            if "{{ session.get('user_id', 0)" in line and not "}}" in line:
                # Check next lines for the broken pattern
                if i+1 < len(lines) and lines[i+1].strip() == "}":
                    if i+2 < len(lines) and lines[i+2].strip() == "};":
                        # Found broken pattern - fix it
                        fixed_line = line.rstrip() + " }};"
                        fixed_lines.append(fixed_line)
                        i += 3  # Skip the broken closing lines
                        fixes += 1
                        print(f"Fixed at line {i-2}")
                        continue
            
            fixed_lines.append(line)
            i += 1
        
        if fixes > 0:
            with open(FILE_PATH, 'w', encoding='utf-8') as f:
                f.write('\n'.join(fixed_lines))
            print(f"Fixed {fixes} occurrences using line-by-line approach.")
        else:
            print("No broken patterns found.")

if __name__ == "__main__":
    fix_all()
