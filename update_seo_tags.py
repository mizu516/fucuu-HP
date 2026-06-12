import os
import re

BASE_DIR = r"g:\マイドライブ\3.Product\fucuu\HP"

def update_seo_tags():
    updated_count = 0
    # Process index.html separately, and also all files in journal and encyclopedia
    target_files = [os.path.join(BASE_DIR, 'index.html')]
    
    for subdir in ['journal', 'encyclopedia']:
        dir_path = os.path.join(BASE_DIR, subdir)
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith('.html'):
                    target_files.append(os.path.join(dir_path, file))
                    
    for filepath in target_files:
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if already has twitter card
        if 'name="twitter:card"' in content:
            continue
            
        # Find the og:type tag to inject after it
        match = re.search(r'<meta property="og:type" content="[^"]+">', content)
        if match:
            og_type_tag = match.group(0)
            replacement = og_type_tag + '\n    <meta name="twitter:card" content="summary_large_image">'
            content = content.replace(og_type_tag, replacement)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            updated_count += 1
            
    print(f"Updated {updated_count} files with Twitter Card tag.")

if __name__ == '__main__':
    update_seo_tags()
