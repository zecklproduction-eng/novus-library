
import os

FILE_PATH = r'd:\nist project\computer\library\novus-library\templates\group.html'

def fix_all_indentation():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    # Lines that start with "    window." (4 spaces) or are inside those functions
    # need to be converted to "        window." (8 spaces)
    # This applies from line 3662 onwards for comment-related functions
    
    in_function_block = False
    function_indent_depth = 0
    
    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.rstrip('\r\n')
        
        # Check if this line defines a window function with only 4-space indent
        if stripped.startswith('    window.') and not stripped.startswith('        '):
            # This is a misindented function - add 4 spaces
            fixed_lines.append('    ' + line)
            in_function_block = True
            function_indent_depth = 1
        elif in_function_block:
            # Check if we're still in a function block with wrong indent
            if stripped.startswith('    ') and not stripped.startswith('        '):
                # Add 4 spaces
                fixed_lines.append('    ' + line)
                
                # Track brace depth
                function_indent_depth += stripped.count('{') - stripped.count('}')
                if function_indent_depth <= 0:
                    in_function_block = False
            else:
                # Already has proper indent or is empty
                fixed_lines.append(line)
                if stripped and function_indent_depth > 0:
                    function_indent_depth += stripped.count('{') - stripped.count('}')
                    if function_indent_depth <= 0:
                        in_function_block = False
        else:
            fixed_lines.append(line)
    
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Fixed indentation for all window functions.")

if __name__ == "__main__":
    fix_all_indentation()
