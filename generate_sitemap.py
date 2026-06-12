import os
import re
import datetime

BASE_DIR = r"g:\マイドライブ\3.Product\fucuu\HP"
BASE_URL = "https://fucuu.jp/"

def extract_date(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Try to find datePublished in JSON-LD
            match = re.search(r'"datePublished":\s*"([^"]+)"', content)
            if match:
                date_str = match.group(1)
                # Ensure it's in YYYY-MM-DD format
                if len(date_str) >= 10:
                    return date_str[:10]
    except Exception as e:
        pass
        
    # Fallback to file modification time
    mtime = os.path.getmtime(filepath)
    return datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

def generate_sitemap():
    urls = []
    
    # Exclude directories
    exclude_dirs = ['.git', '.agents', 'assets']
    
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.html'):
                # テンプレートやGoogleサーチコンソール用ファイルを除外
                if file == 'template.html':
                    continue
                if file.startswith('google') and file.endswith('.html'):
                    continue
                    
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, BASE_DIR).replace('\\', '/')
                
                # Determine URL and Priority
                if rel_path == 'index.html':
                    url = BASE_URL
                    priority = "1.0"
                else:
                    url = BASE_URL + rel_path
                    if 'journal' in rel_path:
                        priority = "0.8"
                    elif 'encyclopedia' in rel_path:
                        priority = "0.7"
                    else:
                        priority = "0.5" # Default for other pages
                        
                lastmod = extract_date(filepath)
                urls.append({'loc': url, 'lastmod': lastmod, 'priority': priority})
                
    # Sort URLs (index first, then by priority, then by date descending)
    urls.sort(key=lambda x: (-float(x['priority']), x['lastmod'] + x['loc']))
    
    # Generate XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    
    for u in urls:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{u["loc"]}</loc>')
        xml_lines.append(f'    <lastmod>{u["lastmod"]}</lastmod>')
        xml_lines.append(f'    <priority>{u["priority"]}</priority>')
        xml_lines.append('  </url>')
        
    xml_lines.append('</urlset>')
    
    sitemap_path = os.path.join(BASE_DIR, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines) + '\n')
        
    print(f"Generated sitemap.xml with {len(urls)} URLs.")

if __name__ == '__main__':
    generate_sitemap()
