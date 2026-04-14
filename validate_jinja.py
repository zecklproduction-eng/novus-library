
import sys
import os
from jinja2 import Environment, FileSystemLoader

def validate_template(filename):
    env = Environment(loader=FileSystemLoader(os.path.dirname(filename)))
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        env.parse(content)
        print(f"✅ {filename}: Syntax OK")
    except Exception as e:
        print(f"❌ {filename}: Error")
        print(e)
        # Attempt to map error to line number
        if hasattr(e, 'lineno'):
            print(f"Line: {e.lineno}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        validate_template(sys.argv[1])
    else:
        print("Usage: python validate_jinja.py <filename>")
