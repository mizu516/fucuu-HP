import os
import re
import random
from bs4 import BeautifulSoup

BASE_DIR = r"g:\マイドライブ\3.Product\fucuu\HP\journal"

def get_all_articles():
    articles = []
    for file in os.listdir(BASE_DIR):
        if file.endswith('.html') and file not in ['index.html', 'template.html']:
            filepath = os.path.join(BASE_DIR, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                title_tag = soup.find('h1')
                title = title_tag.text if title_tag else file
                img_tag = soup.find('img', alt=title)
                img_src = img_tag['src'] if img_tag else f"../assets/journal/{file.replace('.html', '-hero.png')}"
                
                articles.append({
                    'title': title,
                    'url': file,
                    'img_src': img_src
                })
    return articles

def upgrade_articles(all_articles):
    for file in os.listdir(BASE_DIR):
        if file.endswith('.html') and file != 'index.html':
            filepath = os.path.join(BASE_DIR, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            updated = False
            
            # 1. Breadcrumbs
            header = soup.find('header')
            if header and not soup.find('div', class_='breadcrumbs'):
                title_tag = soup.find('h1')
                title = title_tag.text if title_tag else "{{title}}"
                breadcrumbs_html = f'<div class="breadcrumbs"><a href="../index.html">ホーム</a> &gt; <a href="index.html">Journal</a> &gt; <span>{title}</span></div>\n'
                breadcrumbs_soup = BeautifulSoup(breadcrumbs_html, 'html.parser')
                header.insert(0, breadcrumbs_soup)
                updated = True
                
            # 2. Lazy Loading
            journal_content = soup.find('div', class_='journal-content')
            if journal_content:
                for img in journal_content.find_all('img'):
                    if not img.get('loading'):
                        img['loading'] = 'lazy'
                        updated = True
                        
            # 3. Related Articles
            # Ignore template for related articles random logic, just insert placeholder
            if not soup.find('div', class_='related-articles'):
                related_html = '<div class="related-articles"><h3 class="serif">こちらの記事もおすすめ</h3><div class="related-grid">'
                
                if file == 'template.html':
                    related_html += '<!-- Related articles will be generated here -->'
                else:
                    # Pick 3 random articles that are not this one
                    others = [a for a in all_articles if a['url'] != file]
                    if len(others) >= 3:
                        picked = random.sample(others, 3)
                        for p in picked:
                            related_html += f'''
                            <a href="{p['url']}" class="related-card">
                                <img src="{p['img_src']}" alt="{p['title']}" loading="lazy">
                                <div class="related-card-content">
                                    <div class="related-card-title">{p['title']}</div>
                                </div>
                            </a>
                            '''
                
                related_html += '</div></div>'
                related_soup = BeautifulSoup(related_html, 'html.parser')
                
                # Insert before BASE button
                base_button = soup.find(string=lambda text: isinstance(text, str) and 'BASE購入ボタン' in text)
                if base_button:
                    parent_div = base_button.find_parent('div')
                    if not parent_div: # Sometimes it's just a comment
                        parent_div = base_button.next_element
                        while parent_div and parent_div.name != 'div':
                            parent_div = parent_div.next_element
                    
                    if parent_div:
                        parent_div.insert_before(related_soup)
                        updated = True
                        
            if updated:
                with open(filepath, 'w', encoding='utf-8') as f:
                    # Use formatter to avoid messing up script tags too much, but standard str() is safer for some docs
                    # We will use str(soup) to preserve everything as is
                    f.write(str(soup))

def upgrade_index():
    filepath = os.path.join(BASE_DIR, 'index.html')
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    soup = BeautifulSoup(content, 'html.parser')
    updated = False
    
    # 1. Add Filter Buttons
    section_title = soup.find('div', class_='section-title')
    if section_title and not soup.find('div', class_='tag-filters'):
        filters_html = '''
        <div class="tag-filters">
            <button class="tag-filter-btn active" data-tag="all">すべて</button>
            <button class="tag-filter-btn" data-tag="写真">📷 写真</button>
            <button class="tag-filter-btn" data-tag="イラスト">🎨 イラスト</button>
            <button class="tag-filter-btn" data-tag="ハイブリッド">✨ ハイブリッド</button>
        </div>
        '''
        filters_soup = BeautifulSoup(filters_html, 'html.parser')
        section_title.insert_after(filters_soup)
        updated = True

    # 2. Add Lazy loading to all article images (except maybe the first 4)
    articles = soup.find_all('article')
    for i, article in enumerate(articles):
        # assign data-tag for filtering based on the badge
        badge = article.find('span', style=lambda value: value and 'background: #f0f0f0' in value)
        if badge:
            badge_text = badge.text.strip()
            if '写真' in badge_text:
                article['data-tag'] = '写真'
            elif 'イラスト' in badge_text:
                article['data-tag'] = 'イラスト'
            elif 'ハイブリッド' in badge_text:
                article['data-tag'] = 'ハイブリッド'
        else:
            article['data-tag'] = 'all'
            
        # Add a class for JS to target easily
        if 'journal-item' not in article.get('class', []):
            classes = article.get('class', [])
            classes.append('journal-item')
            article['class'] = classes
            
        # Lazy loading
        if i >= 4:
            img = article.find('img')
            if img and not img.get('loading'):
                img['loading'] = 'lazy'
                updated = True
                
    # 3. Add Load More Button
    journal_list = soup.find('div', id='journal-list') or soup.find('div', style=lambda value: value and 'grid-template-columns' in value)
    if journal_list and not soup.find('button', id='loadMoreBtn'):
        load_more_html = '''
        <div class="load-more-container">
            <button id="loadMoreBtn" class="btn">もっと見る</button>
        </div>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const articles = document.querySelectorAll('.journal-item');
                const loadMoreBtn = document.getElementById('loadMoreBtn');
                const filterBtns = document.querySelectorAll('.tag-filter-btn');
                let visibleCount = 9;
                let currentTag = 'all';

                function updateView() {
                    let visibleInCurrentTag = 0;
                    let shownCount = 0;
                    
                    articles.forEach(article => {
                        const tag = article.getAttribute('data-tag');
                        const matchesTag = currentTag === 'all' || tag === currentTag;
                        
                        if (matchesTag) {
                            visibleInCurrentTag++;
                            if (shownCount < visibleCount) {
                                article.classList.remove('hidden-article');
                                shownCount++;
                            } else {
                                article.classList.add('hidden-article');
                            }
                        } else {
                            article.classList.add('hidden-article');
                        }
                    });

                    if (visibleInCurrentTag <= visibleCount) {
                        loadMoreBtn.style.display = 'none';
                    } else {
                        loadMoreBtn.style.display = 'inline-block';
                    }
                }

                if (loadMoreBtn) {
                    loadMoreBtn.addEventListener('click', () => {
                        visibleCount += 9;
                        updateView();
                    });
                }

                filterBtns.forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        filterBtns.forEach(b => b.classList.remove('active'));
                        e.target.classList.add('active');
                        currentTag = e.target.getAttribute('data-tag');
                        visibleCount = 9; // Reset count
                        updateView();
                    });
                });

                // Initial view
                updateView();
            });
        </script>
        '''
        load_more_soup = BeautifulSoup(load_more_html, 'html.parser')
        journal_list.insert_after(load_more_soup)
        updated = True
        
    if updated:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))

if __name__ == "__main__":
    all_articles = get_all_articles()
    print(f"Found {len(all_articles)} articles.")
    upgrade_articles(all_articles)
    print("Upgraded all article pages.")
    upgrade_index()
    print("Upgraded index.html.")
