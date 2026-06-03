import os
import requests
import urllib.parse
from bs4 import BeautifulSoup

def fix_articles():
    index_path = r"g:\マイドライブ\3.Product\fucuu\HP\journal\index.html"
    assets_dir = r"g:\マイドライブ\3.Product\fucuu\HP\assets\journal"
    
    with open(index_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
    articles = soup.find_all('article')
    updated = False
    
    for article in articles:
        # Check if it already has an img
        if article.find('img'):
            continue
            
        print("Found broken article...")
        # Get the slug from the a href
        a_tag = article.find('h3').find('a')
        href = a_tag['href']
        slug = href.replace('.html', '')
        title = a_tag.text.strip()
        
        # Get the badge style
        badge = article.find('span', style=lambda value: value and 'background: #f0f0f0' in value)
        badge_text = badge.text if badge else ""
        
        visual_style = "beautiful calming photo of herbal bath and self care"
        if "イラスト" in badge_text:
            visual_style = "beautiful calming illustration of herbal bath and self care"
        elif "ハイブリッド" in badge_text:
            visual_style = "beautiful calming minimalist art of herbal bath and self care"
            
        # Download image
        print(f"Downloading image for {slug}...")
        encoded_prompt = urllib.parse.quote(visual_style)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=450&nologo=true&seed={hash(slug)}"
        
        img_path = os.path.join(assets_dir, f"{slug}-hero.png")
        if not os.path.exists(img_path):
            try:
                img_data = requests.get(image_url).content
                with open(img_path, 'wb') as img_file:
                    img_file.write(img_data)
                print(f"Saved {slug}-hero.png")
            except Exception as e:
                print(f"Failed to download image: {e}")
                continue
                
        # Fix HTML structure
        # Original contents
        contents = list(article.contents)
        
        # Modify article style
        style = article.get('style', '')
        style = style.replace('padding: 1.5rem;', 'overflow: hidden;')
        article['style'] = style
        
        # Clear article
        article.clear()
        
        # Create image div
        img_div = soup.new_tag('div', style="aspect-ratio: 16/9; overflow: hidden; border-bottom: 1px solid var(--color-border);")
        img_tag = soup.new_tag('img', src=f"../assets/journal/{slug}-hero.png", alt=title, style="width: 100%; height: 100%; object-fit: cover;")
        img_div.append(img_tag)
        article.append(img_div)
        
        # Create padding div
        padding_div = soup.new_tag('div', style="padding: 1.5rem;")
        for c in contents:
            padding_div.append(c)
            
        article.append(padding_div)
        updated = True

    if updated:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(soup.prettify(formatter="html"))
        print("Updated index.html successfully.")
    else:
        print("No broken articles found.")

if __name__ == '__main__':
    fix_articles()
