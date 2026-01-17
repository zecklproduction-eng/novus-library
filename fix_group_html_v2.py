
import os

FILE_PATH = r'd:\nist project\computer\library\novus-library\templates\group.html'

def fix_file():
    if not os.path.exists(FILE_PATH):
        print("File not found.")
        return

    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # The broken block exactly as seen in the file view
    # lines 3526-3528
    broken_lines = [
        "            const currentUserId = window.currentUserId || {{ session.get('user_id', 0)",
        "        }",
        "    };"
    ]
    
    # Construct the block to search for
    # We'll use a slightly more flexible approach by finding the start line index
    lines = content.splitlines()
    found_idx = -1
    
    target_line = "            const currentUserId = window.currentUserId || {{ session.get('user_id', 0)"
    
    for i, line in enumerate(lines):
        if target_line in line:
            # Check if next line is "        }"
            if i+1 < len(lines) and "        }" in lines[i+1]:
                found_idx = i
                print(f"Found broken block starting at line {i+1}")
                break
    
    if found_idx != -1:
        # We found it. Now replace lines found_idx to found_idx+2
        # The replacement should be a single line:
        # const currentUserId = window.currentUserId || {{ session.get('user_id', 0) }};
        # And we might need to remove the next two lines if they are just closing braces that are no longer needed?
        # Wait, the original code had:
        # const currentUserId = window.currentUserId || {{ session.get('user_id', 0)
        #         }
        #     };
        # This looks like it was accidentally split and gained extra braces.
        # The correct line should probably be:
        # const currentUserId = window.currentUserId || {{ session.get('user_id', 0) }};
        
        # So we replace the first line and delete the next two lines.
        
        lines[found_idx] = "            const currentUserId = window.currentUserId || {{ session.get('user_id', 0) }};"
        # Remove the next two lines which are garbage braces
        # verify they are indeed garbage
        if lines[found_idx+1].strip() == "}" and lines[found_idx+2].strip() == "};":
             del lines[found_idx+2]
             del lines[found_idx+1]
        elif lines[found_idx+1].strip() == "}":
             del lines[found_idx+1]
             
        # Join back
        new_content = "\n".join(lines)
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully fixed file.")
    else:
        print("Could not find the specific broken line sequence.")

if __name__ == "__main__":
    fix_file()
