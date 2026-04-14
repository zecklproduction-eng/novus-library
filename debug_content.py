
with open('templates/group.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if i >= 3605 and i <= 3615:
            print(f"{i+1}:{repr(line)}")
