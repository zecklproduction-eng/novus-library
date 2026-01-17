
import jinja2

TEMPLATE_PATH = r'd:\nist project\computer\library\novus-library\templates\group.html'

def check_syntax():
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        env = jinja2.Environment()
        env.parse(content)
        print("Jinja2 Syntax check PASSED.")
    except jinja2.TemplateSyntaxError as e:
        print(f"Jinja2 Error at line {e.lineno}: {e.message}")

if __name__ == "__main__":
    check_syntax()
