import os

files = [
    r'c:\Users\Admin\Desktop\Monicah - Copy\templates\core\landing.html',
    r'c:\Users\Admin\Desktop\Monicah - Copy\templates\users\dashboard_farmer.html',
]

for file_path in files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        skip = False
        for line in lines:
            if "{% url 'feed' %}" in line:
                continue
            # Also remove the stats card in farmer dashboard (simple heuristic)
            if 'Community Posts' in line:
                # This is a bit hacky, but we need to remove the surrounding card.
                # Let's just remove the line for now, or maybe the block if we can identify it.
                # Actually, let's just handle the feed link first.
                pass
            new_lines.append(line)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Processed {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
