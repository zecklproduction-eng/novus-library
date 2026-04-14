import sys
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

def validate_template(filename):
    try:
        env = Environment(loader=FileSystemLoader('.'))
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        env.parse(source)
        print("OK: Template is valid.")
    except TemplateSyntaxError as e:
        print(f"ERROR: {e.message} at line {e.lineno}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    validate_template(sys.argv[1])
