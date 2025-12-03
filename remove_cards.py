import os

def remove_block(file_path, start_marker, end_marker):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        in_block = False
        block_removed = False
        
        for line in lines:
            if start_marker in line and not block_removed:
                in_block = True
                continue
            
            if in_block:
                if end_marker in line:
                    in_block = False
                    block_removed = True
                continue
            
            new_lines.append(line)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Processed {file_path}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Remove Community Card from Landing Page
remove_block(
    r'c:\Users\Admin\Desktop\Monicah - Copy\templates\core\landing.html',
    '<!-- Community Card -->',
    '<!-- AI Assistant Card -->' # We can use the next card as a stopper if we are careful, or just count divs.
    # Actually, the previous attempt showed the structure. 
    # Let's use a more specific approach for the block.
)

# Let's rewrite the function to be more specific based on the content I saw.
def remove_community_card_landing():
    file_path = r'c:\Users\Admin\Desktop\Monicah - Copy\templates\core\landing.html'
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    skip = False
    for line in lines:
        if '<!-- Community Card -->' in line:
            skip = True
        if '<!-- AI Assistant Card -->' in line:
            skip = False
        
        if not skip:
            new_lines.append(line)
            
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Processed landing.html")

def remove_community_stats_farmer():
    file_path = r'c:\Users\Admin\Desktop\Monicah - Copy\templates\users\dashboard_farmer.html'
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    skip = False
    # We look for the specific stats card structure
    # It starts with <div class="col-md-3"> and contains "Community Posts"
    # This is tricky line-by-line.
    # Let's load the whole content and use string replacement or regex.
    
    content = "".join(lines)
    
    # Define the block to remove based on what we saw in view_file
    # We need to be careful with whitespace.
    # I'll try to find the block by its unique content and remove the surrounding div.
    
    # Heuristic: Find the line with "Community Posts", then find the opening div before it and closing div after it.
    # Since I know the structure is standard (col-md-3 -> card -> card-body), I can try to remove the specific chunk.
    
    # Let's try to identify the block by the "Community Posts" text and remove the 8 lines around it?
    # No, that's dangerous.
    
    # Let's use the exact lines we saw in view_file, assuming they are contiguous.
    pass

if __name__ == "__main__":
    remove_community_card_landing()
    
    # For farmer dashboard, I'll read it, find the index of "Community Posts", 
    # and then identify the start and end of that card block.
    file_path = r'c:\Users\Admin\Desktop\Monicah - Copy\templates\users\dashboard_farmer.html'
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    new_lines = []
    i = 0
    while i < len(lines):
        # Check if this looks like the start of the community stats card
        # It was around line 29 in view_file
        # <div class="col-md-3">
        #     <div class="card stat-card border-0">
        #         <div class="card-body text-center">
        #             <i class="bi bi-chat-left-text text-primary" style="font-size: 2rem;"></i>
        #             <h3 class="text-primary mt-2">{{ user.posts.count }}</h3>
        #             <p class="text-muted mb-0">Community Posts</p>
        #         </div>
        #     </div>
        # </div>
        
        if 'Community Posts' in lines[i+6] if i+6 < len(lines) else False:
             # Found the line inside.
             # The block starts 6 lines back (approx) and ends 2 lines forward.
             # Let's verify:
             # i: <div class="col-md-3">
             # i+1: <div class="card ...">
             # i+2: <div class="card-body ...">
             # i+3: <i ...>
             # i+4: <h3 ...>
             # i+5: <p ...>Community Posts</p>
             # i+6: </div>
             # i+7: </div>
             # i+8: </div>
             
             # Wait, "Community Posts" is on line 34 in view_file.
             # Start is line 29. 34-29 = 5.
             # So if lines[i+5] has "Community Posts", then lines[i] is the start.
             pass
        
        # Let's just look for the specific block signature
        if 'Community Posts' in lines[i]:
            # We found the text. We need to remove the lines around it.
            # We need to remove from i-5 to i+3 (inclusive) based on the structure.
            # But we are iterating.
            # Let's do a second pass or just filter.
            pass
            
    # Simpler: Read content, split by "Community Posts", find the last <div class="col-md-3"> before it and the first </div></div></div> after it.
    # This is getting complicated for a script.
    
    # Let's rely on the fact that I have the EXACT content from view_file and use python replace.
    
    content = "".join(lines)
    
    block_to_remove = """    <div class="col-md-3">
        <div class="card stat-card border-0">
            <div class="card-body text-center">
                <i class="bi bi-chat-left-text text-primary" style="font-size: 2rem;"></i>
                <h3 class="text-primary mt-2">{{ user.posts.count }}</h3>
                <p class="text-muted mb-0">Community Posts</p>
            </div>
        </div>
    </div>
"""
    # Normalize line endings just in case
    content = content.replace(block_to_remove, "")
    
    # Also try with different indentation if that failed
    block_to_remove_2 = """    <div class="col-md-3">
        <div class="card stat-card border-0">
            <div class="card-body text-center">
                <i class="bi bi-chat-left-text text-primary" style="font-size: 2rem;"></i>
                <h3 class="text-primary mt-2">{{ user.posts.count }}</h3>
                <p class="text-muted mb-0">Community Posts</p>
            </div>
        </div>
    </div>""" # No newline at end
    
    content = content.replace(block_to_remove_2, "")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Processed dashboard_farmer.html")
