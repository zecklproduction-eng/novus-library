
import os

FILE_PATH = r'd:\nist project\computer\library\novus-library\templates\group.html'

def fix_indentation():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Lines 3581-3659 (0-indexed: 3580-3658) need to be indented by 8 more spaces
    # But we need to be careful - line 3660 (0-indexed: 3659) has a closing brace that also needs fixing
    
    fixed_lines = []
    in_broken_section = False
    
    for i, line in enumerate(lines):
        line_num = i + 1  # 1-indexed for readability
        
        # Start of broken section after currentUserId line
        if line_num == 3581:
            in_broken_section = True
        
        # End of broken section at the catch block's closing brace
        # Line 3659 has "    }" which should be "            }"
        # Line 3660 has "        }" which closes loadComments - this one is correct
        if line_num == 3660:
            in_broken_section = False
        
        if in_broken_section and line.startswith('    ') and not line.startswith('        '):
            # Add 8 spaces to fix indentation
            fixed_lines.append('        ' + line)
        else:
            fixed_lines.append(line)
    
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Fixed indentation for loadComments function.")

if __name__ == "__main__":
    fix_indentation()
