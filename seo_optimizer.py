import os
import re
import glob
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
from PIL import Image

BASE_DIR = Path(r"g:\マイドライブ\3.Product\fucuu\HP")

# 1. Convert Images to WebP
def convert_to_webp():
    print("Converting images to WebP...")
    assets_dir = BASE_DIR / "assets"
    
    # Find all PNG/JPG images
    image_paths = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        image_paths.extend(assets_dir.rglob(ext))
        
    for img_path in image_paths:
        try:
            with Image.open(img_path) as img:
                webp_path = img_path.with_suffix('.webp')
                img.save(webp_path, 'WEBP', quality=85)
            # Remove original to save space
            img_path.unlink()
            print(f"Converted {img_path.name} to WebP")
        except Exception as e:
            print(f"Error converting {img_path}: {e}")

# Replace text references
def replace_image_extensions():
    print("Updating image references in HTML/CSS/XML...")
    extensions_to_replace = ['.png', '.jpg', '.jpeg']
    
    # Target files
    target_files = []
    target_files.extend(BASE_DIR.glob('*.html'))
    target_files.extend(BASE_DIR.glob('*.css'))
    target_files.extend(BASE_DIR.glob('*.xml'))
    target_files.extend((BASE_DIR / 'journal').glob('*.html'))
    target_files.extend((BASE_DIR / 'encyclopedia').glob('*.html'))
    
    for filepath in target_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            # Simple string replace for .png, .jpg
            for ext in extensions_to_replace:
                # To avoid matching things like .png in text, we can be a bit more specific or just replace all .png" and .png' and .png)
                # But a simple replace of '.png"' -> '.webp"', '.png'' -> '.webp'', '.png)' -> '.webp)'
                # Actually, replacing all .png with .webp is usually safe for these static assets
                content = re.sub(re.escape(ext) + r'([\s"\'\)])', r'.webp\1', content, flags=re.IGNORECASE)
                
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
        except Exception as e:
            print(f"Error updating {filepath}: {e}")

# 2. Internal Linking for Journal
def build_internal_links():
    print("Building internal links in journal articles...")
    herbs = {
        'トウキ': 'touki.html',
        '当帰': 'touki.html',
        'チンピ': 'chinpi.html',
        '陳皮': 'chinpi.html',
        'ガイヨウ': 'gaiyo.html',
        '艾葉': 'gaiyo.html',
        'ケイヒ': 'keihi.html',
        '桂皮': 'keihi.html',
        'シナモン': 'keihi.html',
        'カミツレ': 'kamitsure.html',
        'カモミール': 'kamitsure.html',
        'ジュウヤク': 'juyaku.html',
        'ドクダミ': 'juyaku.html',
        'サンシン': 'sanshin.html',
        'クチナシ': 'sanshin.html',
        'センキュウ': 'senkyu.html',
        '川キュウ': 'senkyu.html',
        'ショウブ根': 'shobukon.html',
        '菖蒲根': 'shobukon.html',
        'ウイキョウ': 'uikyo.html',
        'フェンネル': 'uikyo.html'
    }
    
    journal_dir = BASE_DIR / 'journal'
    for filepath in journal_dir.glob('*.html'):
        if filepath.name in ['index.html', 'template.html']:
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            
        content_div = soup.find('div', class_='journal-content')
        if not content_div:
            continue
            
        updated = False
        linked_herbs = set() # Link only once per herb per article
        
        # We need to find text nodes and replace keywords with <a> tags
        for text_node in content_div.find_all(string=True):
            if text_node.parent.name in ['a', 'script', 'style', 'h1', 'h2']:
                continue
                
            text = str(text_node)
            new_text = text
            
            for herb, target in herbs.items():
                if target in linked_herbs:
                    continue # Already linked this herb page in this article
                
                if herb in new_text:
                    link_html = f'<a href="../encyclopedia/{target}" style="color: var(--color-primary); text-decoration: underline;">{herb}</a>'
                    # Use a trick: split and join to replace only the first occurrence or all. Let's do all in this node
                    new_text = new_text.replace(herb, link_html, 1)
                    linked_herbs.add(target)
                    updated = True
                    
            if new_text != text:
                new_soup = BeautifulSoup(new_text, 'html.parser')
                text_node.replace_with(new_soup)
                
        if updated:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
                
# 3. Add Structured Data to Encyclopedia
def add_encyclopedia_schema():
    print("Adding structured data to encyclopedia pages...")
    encyclopedia_dir = BASE_DIR / 'encyclopedia'
    for filepath in encyclopedia_dir.glob('*.html'):
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            
        if soup.find('script', type='application/ld+json'):
            continue # Already has schema
            
        title_tag = soup.find('title')
        title = title_tag.text.replace(' | 生薬図鑑 | fucuu (フクウ)', '') if title_tag else ''
        
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        description = desc_tag['content'] if desc_tag else ''
        
        url = f"https://fucuu.jp/encyclopedia/{filepath.name}"
        
        schema_json = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "mainEntityOfPage": {{
        "@type": "WebPage",
        "@id": "{url}"
      }},
      "headline": "{title}の効能と活用法",
      "description": "{description}",
      "author": {{
        "@type": "Organization",
        "name": "fucuu (フクウ)"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "fucuu (フクウ)",
        "logo": {{
          "@type": "ImageObject",
          "url": "https://fucuu.jp/assets/brand_logo.webp"
        }}
      }}
    }}
    </script>
        """
        
        head = soup.find('head')
        if head:
            schema_soup = BeautifulSoup(schema_json, 'html.parser')
            head.append(schema_soup)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))

if __name__ == "__main__":
    convert_to_webp()
    replace_image_extensions()
    build_internal_links()
    add_encyclopedia_schema()
    print("SEO Optimization Complete.")
