import os
import datetime
import json
import re
import random
import google.generativeai as genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests

# 環境変数の読み込み
load_dotenv()

# 設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY") # オプション
MODEL_NAME = 'models/gemini-flash-latest'
TEMPLATE_PATH = "../../journal/template.html"
INDEX_PATH = "../../journal/index.html"
SITEMAP_PATH = "../../sitemap.xml"
OUTPUT_DIR = "../../journal/"
HISTORY_PATH = "logs/article_history.json"

# ブランド情報
BRAND_VOICE = """
ブランド名: fucuu (フクウ)
コンセプト: 植物のちからで 'わたしに戻る' 時間。生薬入浴剤と国産アロマ。
トーン: 穏やか、温かい、専門的だが親しみやすい、幸福感（フクフク）。
キーワード: 生薬, 温活, セルフケア, 養生, 無添加, 100%天然。
"""

genai.configure(api_key=GEMINI_API_KEY)

def get_automated_topic():
    """AIに本日のトレンドやブランドに適したトピックを提案させる"""
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"""
    あなたはセルフケアブランド「fucuu」の編集長です。
    今日（{datetime.date.today()}）にふさわしい、読者が読みたくなるブログ（Journal）のテーマを1つ提案してください。
    
    【要件】
    - 季節感や現代人の悩み（疲れ、冷え、不眠など）に寄り添ったもの。
    - 具体的で、検索されやすいキーワードを含める。
    - ブランドコンセプト「植物のちからでわたしに戻る時間」に合致するもの。
    
    出力形式: "キーワード/タイトル案" の形式で一行で出力してください。
    例: 温活 入浴剤/心まで温める、冬の夜の生薬入浴法
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def generate_article_content(topic_info):
    """
    記事内容と「ビジュアルスタイル」をAIに決定させる
    """
    # 既存の履歴から過去のスタイルを確認（A/Bテスト用）
    visual_styles = ["photo", "illustration", "hybrid"]
    chosen_style = random.choice(visual_styles)
    
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"""
    あなたはセルフケアブランド「fucuu」の専属ライターです。
    以下のテーマに基づき、読者の悩みを解決しつつブランドの世界観を伝えるSEOブログ記事を執筆してください。

    テーマ: {topic_info}
    ビジュアルスタイル: {chosen_style} (これに合わせて挿絵の指示を入れてください)
    {BRAND_VOICE}

    【執筆ルール】
    1. 構成: 導入、3つの見出し(H2)、具体的なTips(H3)、まとめ。
    2. 文字数: 1500〜2000文字程度。
    3. 特殊タグの活用:
       - 非常に重要な箇所は <span class="highlight-text">...</span> で囲む。
       - 役立つアドバイスは <div class="tip-box"><h4>Tips</h4><p>...</p></div> で囲む。
       - 本文中の適切な箇所に [IMAGE: 説明文] という形式で、その場にふさわしい画像の指示を1〜2箇所入れてください。
    4. 出力形式: JSON形式で出力してください。
    
    JSON構造:
    {{
      "title": "記事のタイトル",
      "description": "メタディスクリプション (120文字程度)",
      "slug": "url-slug",
      "content": "HTML形式の本文",
      "keywords": "SEOキーワード",
      "featured_image_prompt": "アイキャッチ画像用の英語の検索/生成プロンプト (例: beautiful calming botanical photo of lavender field)",
      "visual_style": "{chosen_style}"
    }}
    """
    response = model.generate_content(prompt)
    # JSONの抽出
    json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
    data = json.loads(json_str)
    data['visual_style'] = chosen_style # 念のため
    return data

def get_image_url(slug, index=0, style="photo"):
    """
    Previously used Unsplash Source, which is now deprecated.
    Now follows a local naming convention.
    """
    if index == 0:
        return f"../assets/journal/{slug}-hero.png"
    return f"../assets/journal/{slug}-{index}.png"

def create_html(article_data):
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()
    
    date_str = datetime.date.today().strftime("%Y.%m.%d")
    
    # 画像の取得（ローカルパス運用に変更）
    slug = article_data['slug']
    featured_img = f"../assets/journal/{slug}-hero.png"

    # 本文内の [IMAGE: ...] タグをローカル画像タグに置換
    content = article_data['content']
    image_tags = re.findall(r'\[IMAGE: (.*?)\]', content)
    for i, img_desc in enumerate(image_tags):
        # 1から始まるインデックス
        img_url = f"../assets/journal/{slug}-{i+1}.png"
        replacement = f"""
        <div class="blog-image">
            <img src="{img_url}" alt="{img_desc}">
        </div>
        """
        content = content.replace(f"[IMAGE: {img_desc}]", replacement)

    date_iso = datetime.date.today().isoformat()
    featured_img_url = f"https://fucuu.jp/assets/journal/{slug}-hero.png"

    html = template.replace("{{title}}", article_data['title'])
    html = html.replace("{{description}}", article_data['description'])
    html = html.replace("{{slug}}", article_data['slug'])
    html = html.replace("{{date}}", date_str)
    html = html.replace("{{date_iso}}", date_iso)
    html = html.replace("{{content}}", content)
    html = html.replace("{{featured_image}}", featured_img)
    html = html.replace("{{featured_image_url}}", featured_img_url)
    
    file_name = f"{article_data['slug']}.html"
    with open(os.path.join(OUTPUT_DIR, file_name), 'w', encoding='utf-8') as f:
        f.write(html)
    
    return file_name

def update_index(article_data, file_name):
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    list_div = soup.find(id='journal-list')
    if not list_div:
        # 万が一IDがない場合のフォールバック（旧構造）
        list_div = soup.find('div', class_='journal-grid')
        
    # 初期メッセージの削除
    if list_div and "記事を準備中です" in list_div.get_text():
        list_div.clear()
    
    # 新しい記事カードの追加
    date_str = datetime.date.today().strftime("%Y.%m.%d")
    new_card = soup.new_tag('article', style="border: 1px solid var(--color-border); padding: 1.5rem; transition: var(--transition-base);")
    
    # ビジュアルスタイルのラベルを表示（デバッグ兼ねて）
    style_label = "📷 写真" if article_data['visual_style'] == "photo" else "🎨 イラスト" if article_data['visual_style'] == "illustration" else "✨ ハイブリッド"
    
    # Download image using pollinations.ai
    prompt_text = article_data.get('featured_image_prompt', f"calming {article_data['visual_style']} of herbal bath and self care")
    encoded_prompt = requests.utils.quote(prompt_text)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=450&nologo=true"
    
    try:
        img_data = requests.get(image_url).content
        with open(os.path.join("../../assets/journal", f"{article_data['slug']}-hero.png"), 'wb') as img_file:
            img_file.write(img_data)
    except Exception as e:
        print(f"Failed to download image: {e}")
        
    new_card.append(BeautifulSoup(f"""
        <div style="aspect-ratio: 16/9; overflow: hidden; border-bottom: 1px solid var(--color-border);">
            <img src="../assets/journal/{article_data['slug']}-hero.png" alt="{article_data['title']}" style="width: 100%; height: 100%; object-fit: cover;">
        </div>
        <div style="padding: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 0.8rem; color: var(--color-text-light);">{date_str}</span>
                <span style="font-size: 0.7rem; background: #f0f0f0; padding: 2px 8px; border-radius: 10px;">{style_label}</span>
            </div>
            <h3 style="font-size: 1.2rem; margin: 0.5rem 0;"><a href="{file_name}">{article_data['title']}</a></h3>
            <p style="font-size: 0.85rem; color: var(--color-text-light);">{article_data['description']}</p>
            <a href="{file_name}" class="link-arrow" style="margin-top: 1rem; display: inline-block;">読む</a>
        </div>
    """, 'html.parser'))
    
    if list_div:
        list_div.insert(0, new_card)
    
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

def update_sitemap(slug):
    if not os.path.exists(SITEMAP_PATH): return
    with open(SITEMAP_PATH, 'r', encoding='utf-8') as f:
        sitemap = f.read()
    
    if f"journal/{slug}.html" in sitemap: return # 既にあればスキップ
    
    new_url = f"""  <url>
    <loc>https://fucuu.jp/journal/{slug}.html</loc>
    <lastmod>{datetime.date.today().isoformat()}</lastmod>
    <priority>0.8</priority>
  </url>
</urlset>"""
    
    sitemap = sitemap.replace("</urlset>", new_url)
    
    with open(SITEMAP_PATH, 'w', encoding='utf-8') as f:
        f.write(sitemap)

def save_to_history(article_data, file_name):
    history = []
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    history.append({
        "title": article_data['title'],
        "slug": article_data['slug'],
        "date": datetime.date.today().isoformat(),
        "keywords": article_data['keywords'],
        "file_name": file_name,
        "visual_style": article_data.get('visual_style', 'photo'),
        "score": 0
    })
    
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    import sys
    
    # 1. トピックの決定
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
    else:
        print("Automatic topic discovery...")
        keyword = get_automated_topic()
        
    print(f"Target: {keyword}")
    
    try:
        # 2. 記事生成
        print("Generating rich content...")
        article = generate_article_content(keyword)
        print(f"Title: {article['title']}")
        print(f"Style: {article['visual_style']}")
        
        # 3. ファイル作成 & 更新
        fname = create_html(article)
        update_index(article, fname)
        update_sitemap(article['slug'])
        save_to_history(article, fname)
        print(f"\nDone! Article created at: journal/{fname}")
        
        # 4. デプロイ確認
        # 自動化モードの場合は、引数（例: --auto）があれば勝手にデプロイするようにしてもよい
        if "--auto" in sys.argv:
            deploy = True
        else:
            choice = input("\nDeploy to GitHub? (y/n): ")
            deploy = choice.lower() == 'y'
            
        if deploy:
            print("Deploying...")
            # Windowsのos.systemではダブルクォートを使用
            os.system('cd ../.. && git add . && git commit -m "Auto-publish rich blog" && git push origin main')
            print("Successfully published!")
            
    except Exception as e:
        print(f"Error occurred: {e}")
