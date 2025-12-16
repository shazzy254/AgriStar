
import re
import os

files_to_fix = [
    r'c:\Users\Admin\Desktop\monica\templates\users\profile_display.html',
    r'c:\Users\Admin\Desktop\monica\templates\users\farmer_profile_public.html',
    r'c:\Users\Admin\Desktop\monica\templates\users\dashboard_farmer.html'
]

def fix_file(filepath):
    print(f"Fixing {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Regex to find django tags {{ ... }} that might be split across lines
        # We capture {{ then any whitespace/newline then content then whitespace/newline then }}
        # And replace with {{ content }} on single line
        
        def replace_match(match):
            inner = match.group(1)
            # Remove newlines and extra spaces from inner content
            clean_inner = re.sub(r'\s+', ' ', inner).strip()
            return f"{{{{ {clean_inner} }}}}"

        # Standard variable tags
        new_content = re.sub(r'\{\{\s*([^}]+?)\s*\}\}', replace_match, content, flags=re.DOTALL)

        # Fix split widthratio tags
        def replace_widthratio(match):
            inner = match.group(1)
            clean_inner = re.sub(r'\s+', ' ', inner).strip()
            return f"{{% widthratio {clean_inner} %}}"
            
        new_content = re.sub(r'\{%\s*widthratio\s+([^%]+?)\s*%\}', replace_widthratio, new_content, flags=re.DOTALL)
        
        if content != new_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed {filepath}")
        else:
            print(f"No changes needed for {filepath}")
            
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")

if __name__ == "__main__":
    for f in files_to_fix:
        if os.path.exists(f):
            fix_file(f)
        else:
            print(f"File not found: {f}")
