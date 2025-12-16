
file_path = r"C:\Users\Admin\AgriStar\templates\marketplace\cart.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the split template tag
old_text = """Your order will be split into {{ grouped_items|length }} separate order{{
                        grouped_items|length|pluralize }} (one per farmer)"""

new_text = """Your order will be split into {{ grouped_items|length }} separate order{{ grouped_items|length|pluralize }} (one per farmer)"""

if old_text in content:
    content = content.replace(old_text, new_text)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed the split template tag!")
else:
    print("Pattern not found. Trying alternative...")
    # Try with normalized whitespace
    content_normalized = content.replace('\r\n', '\n')
    old_normalized = old_text.replace('\r\n', '\n')
    
    if old_normalized in content_normalized:
        content_normalized = content_normalized.replace(old_normalized, new_text)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content_normalized)
        print("Fixed with normalized line endings!")
    else:
        print("Still not found. Showing actual content around line 169:")
        lines = content.split('\n')
        for i in range(165, 175):
            if i < len(lines):
                print(f"{i}: {repr(lines[i])}")
