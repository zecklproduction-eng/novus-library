
original = """            const currentUserId = window.currentUserId || {{ session.get('user_id', 0)
        }
    };
"""

replacement = """            const currentUserId = window.currentUserId || {{ session.get('user_id', 0) }};
"""

filename = 'templates/group.html'

with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

if original in content:
    new_content = content.replace(original, replacement)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fixed.")
else:
    print("Original text not found.")
    # Debug info
    print("Searching for:")
    print(repr(original))
