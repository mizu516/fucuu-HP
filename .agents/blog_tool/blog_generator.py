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
    - 季節感や現代人の具体的な悩み（「なんとなく疲れが取れない」「寝ても眠い」「手足だけ冷える」など）に寄り添ったもの。
    - 「なぜそうなるのか」という原因の解説＋「今日からできる具体的な対処法」の両方が書けるテーマを選ぶ。
    - Googleで検索されやすい具体的なキーワードを含める（例：「自律神経 整える 入浴」「冷え性 根本原因」など）。
    - ブランドコンセプト「植物のちからでわたしに戻る時間」に合致するもの。
    - 抽象的なテーマ（「心を大切に」など）は避け、体の具体的な不調にフォーカスする。

    出力形式: "キーワード/タイトル案" の形式で一行で出力してください。
    例: 温活 入浴剤/心まで温める、冬の夜の生薬入浴法
    """
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                import time
                print("  API制限に到達しました。60秒待機して再試行します...")
                time.sleep(60)
            else:
                raise e
    raise Exception("トピック生成に失敗しました")

def generate_article_content(topic_info):
    """
    記事内容と「ビジュアルスタイル」をAIに決定させる
    """
    visual_styles = ["photo", "illustration", "hybrid"]
    chosen_style = random.choice(visual_styles)

    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"""
    あなたはセルフケアブランド「fucuu」の専属ライターであり、東洋医学・自律神経・生薬の専門家です。
    以下のテーマに基づき、読者の深い悩みを解決する、専門性の高いSEOブログ記事を執筆してください。

    テーマ: {topic_info}
    ビジュアルスタイル: {chosen_style}
    {BRAND_VOICE}

    【執筆ルール】

    1. 目的とスタンス:
       読者の「悩み解決」を100%最優先にしてください。医学的・科学的に正確な情報のみ書くこと。
       不確かな民間療法や根拠のない情報は絶対に書かないでください。

    2. 構成と深さの基準（これ以下の深さは禁止）:

       ■ 導入（200文字以上）
       - 読者の悩みを具体的に言い当てる。「なんとなく疲れる」ではなく「朝起きた瞬間からすでに疲れている」レベルで描写する。
       - 「あ、私のことだ」と感じさせること。

       ■ 原因の解説（400文字以上）
       - 「なぜその不調が起きるのか」を体のメカニズムから説明する。
       - 例：「交感神経が過剰に働くと血管が収縮し、末梢まで血液が届かなくなります。老廃物が溜まり、それが慢性的な疲労感や冷えの正体です。」
       - このレベルの具体性・深さで書くこと。東洋医学（気血水・経絡など）の視点も加えると独自性が出る。

       ■ 解決策3選（各200文字以上、合計600文字以上）
       - 「明日からすぐ無料でできる」具体的なアクションを3つ。
       - 各アクションに「手順（どこを・何秒・どう）」と「なぜ効くのか（根拠）」を必ずセットで書くこと。
       - 例：「足首の内くるぶしから指4本上にある『三陰交』を親指で3秒押して離す、を10回繰り返します。このツボは肝・脾・腎の3つの経絡が交わる点で、体全体の血流と水分代謝を整える効果があります。」
       - 「深呼吸しましょう」「ゆっくり休みましょう」などの根拠のない浅い提案は絶対禁止。

       ■ まとめとfucuuからの提案（200文字以上）
       - 記事の内容をコンパクトに振り返り、読者に「今日から試せる」という前向きな気持ちを残す。
       - 最後に「忙しくてセルフケアの時間が取れない日は、fucuuの100%生薬入浴剤に頼るのもひとつの選択肢です」と、押し付けがましくなく自然に添える。

    3. 文字数: 合計2000〜2500文字。

    4. 特殊タグの活用:
       - 特に重要な知識・事実は <span class="highlight-text">...</span> で囲む。
       - 今日からできる実践アドバイスは <div class="tip-box"><h4>実践のヒント</h4><p>...</p></div> で囲む。
       - 本文の適切な箇所に [IMAGE: 画像の説明（英語）] を2箇所入れること。説明は具体的に（例: [IMAGE: close-up of a woman pressing acupressure point on her ankle, soft natural lighting]）。

    5. 出力形式: JSON形式のみで出力してください。JSON以外の文章は一切不要。

    JSON構造:
    {{
      "title": "読者が思わずクリックしたくなる記事タイトル",
      "description": "メタディスクリプション（120文字程度・検索結果に表示される要約）",
      "slug": "url用スラッグ（英語・ハイフン区切り）",
      "content": "HTML形式の本文（上記の構成・文字数を厳守）",
      "keywords": "SEOキーワード（カンマ区切り）",
      "featured_image_prompt": "アイキャッチ画像用の英語プロンプト（具体的に。例: serene japanese bath ritual with botanical herbs, warm soft light, minimal aesthetic）",
      "inline_image_prompts": ["インライン画像1の英語プロンプト", "インライン画像2の英語プロンプト"],
      "visual_style": "{chosen_style}"
    }}
    """
    response = None
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            break
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                import time
                print("  API制限に到達しました。60秒待機して再試行します...")
                time.sleep(60)
            else:
                raise e
    
    if not response:
        raise Exception("記事生成に失敗しました")

    json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
    data = json.loads(json_str)
    data['visual_style'] = chosen_style
    return data

def generate_and_save_image(prompt_text, output_path, width=800, height=450):
    """Unsplash から記事に合った高品質な写真を取得してローカルに保存する"""
    from PIL import Image
    import io
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not unsplash_key:
        print(f"  UNSPLASH_ACCESS_KEY が設定されていません。スキップします。")
        return
    try:
        print(f"  画像取得中: {os.path.basename(output_path)} ...")
        search_url = "https://api.unsplash.com/photos/random"
        params = {
            "query": prompt_text,
            "orientation": "landscape",
            "content_filter": "high",
        }
        headers = {"Authorization": f"Client-ID {unsplash_key}"}
        res = requests.get(search_url, params=params, headers=headers, timeout=30)
        res.raise_for_status()
        photo = res.json()
        # 指定サイズでダウンロード
        img_url = photo["urls"]["raw"] + f"&w={width}&h={height}&fit=crop&auto=format&q=85"
        img_data = requests.get(img_url, timeout=30).content
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        img.save(output_path, 'WEBP', quality=85)
        # Unsplash 利用規約に従いダウンロードイベントを通知
        requests.get(photo["links"]["download_location"], headers=headers, timeout=10)
        print(f"  保存完了: {output_path} (撮影者: {photo['user']['name']})")
    except Exception as e:
        print(f"  画像取得に失敗しました ({os.path.basename(output_path)}): {e}")

def create_html(article_data):
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()
    
    date_str = datetime.date.today().strftime("%Y.%m.%d")
    
    # 画像の取得（ローカルパス運用に変更）
    slug = article_data['slug']
    featured_img = f"../assets/journal/{slug}-hero.webp"

    # 本文内の [IMAGE: ...] タグをローカル画像タグに置換
    content = article_data['content']
    image_tags = re.findall(r'\[IMAGE: (.*?)\]', content)
    for i, img_desc in enumerate(image_tags):
        # 1から始まるインデックス
        img_url = f"../assets/journal/{slug}-{i+1}.webp"
        replacement = f"""
        <div class="blog-image">
            <img src="{img_url}" alt="{img_desc}">
        </div>
        """
        content = content.replace(f"[IMAGE: {img_desc}]", replacement)

    date_iso = datetime.date.today().isoformat()
    featured_img_url = f"https://fucuu.jp/assets/journal/{slug}-hero.webp"

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
    
    style_label = "📷 写真" if article_data['visual_style'] == "photo" else "🎨 イラスト" if article_data['visual_style'] == "illustration" else "✨ ハイブリッド"

    new_card.append(BeautifulSoup(f"""
        <div style="aspect-ratio: 16/9; overflow: hidden; border-bottom: 1px solid var(--color-border);">
            <img src="../assets/journal/{article_data['slug']}-hero.webp" alt="{article_data['title']}" style="width: 100%; height: 100%; object-fit: cover;">
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

def update_rss(article_data):
    rss_path = "../../rss.xml"
    if not os.path.exists(rss_path): return
    with open(rss_path, 'r', encoding='utf-8') as f:
        rss = f.read()
    
    date_str = datetime.date.today().strftime("%Y.%m.%d")
    new_item = f"""  <item>
    <title>{article_data['title']}</title>
    <link>https://fucuu.jp/journal/{article_data['slug']}.html</link>
    <description>{article_data['description']}</description>
    <pubDate>{date_str}</pubDate>
  </item>
"""
    
    rss = rss.replace("<channel>", f"<channel>\n{new_item}")
    with open(rss_path, 'w', encoding='utf-8') as f:
        f.write(rss)

def ping_google_sitemap():
    try:
        print("Pinging Google with new sitemap...")
        response = requests.get("https://www.google.com/ping?sitemap=https://fucuu.jp/sitemap.xml")
        if response.status_code == 200:
            print("Successfully pinged Google!")
        else:
            print(f"Ping failed with status code {response.status_code}")
    except Exception as e:
        print(f"Error pinging Google: {e}")

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

        # 3. 画像生成（ヒーロー画像 + 本文内インライン画像）
        print("\n--- 画像を生成しています ---")
        slug = article['slug']
        assets_dir = "../../assets/journal"

        # ヒーロー画像
        hero_prompt = article.get('featured_image_prompt', f"calming botanical herbal bath self care, soft natural light, minimal japanese aesthetic")
        generate_and_save_image(hero_prompt, os.path.join(assets_dir, f"{slug}-hero.webp"), width=800, height=450)

        # 本文内インライン画像（[IMAGE: ...] タグから取得）
        inline_prompts = article.get('inline_image_prompts', [])
        if not inline_prompts:
            # フォールバック：本文中の [IMAGE: ...] タグから直接取得
            inline_prompts = re.findall(r'\[IMAGE: (.*?)\]', article['content'])
        for i, img_prompt in enumerate(inline_prompts, 1):
            generate_and_save_image(img_prompt, os.path.join(assets_dir, f"{slug}-{i}.webp"), width=1200, height=675)

        # 4. ファイル作成 & 更新
        fname = create_html(article)
        update_index(article, fname)
        update_sitemap(article['slug'])
        update_rss(article)
        save_to_history(article, fname)
        print(f"\nDone! Article created at: journal/{fname}")
        
        # 4. デプロイ確認
        if "--auto" in sys.argv:
            deploy = True
        else:
            choice = input("\nDeploy to GitHub? (y/n): ")
            deploy = choice.lower() == 'y'
            
        if deploy:
            print("Deploying...")
            os.system('cd ../.. && git add . && git commit -m "Auto-publish rich blog" && git push origin main')
            print("Successfully published!")
            ping_google_sitemap()
            
    except Exception as e:
        print(f"Error occurred: {e}")
