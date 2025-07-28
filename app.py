import streamlit as st
import openai
import base64
import os
import urllib.parse
import re


# 背景画像の設定
def set_bg(png_file):
    with open(png_file, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: url('data:image/png;base64,{b64}');
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp p, .stApp label, .stApp span {{
        color: #1a237e !important;
        background: #fff !important;
        border-radius: 8px;
        padding: 0.2em 0.5em;
        display: inline-block;  /* ←ここをinline-blockからinlineに変更 */
    }}
    /* st.markdownで出力される材料リストなどにも背景色を適用 */
    .stApp ul, .stApp ol, .stApp li, .stApp pre, .stApp code {{
        background: #fff !important;
        color: #1a237e !important;
        border-radius: 8px;
        padding: 0.2em 0.5em;
        display: inline-block;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# 画像ファイル名（同じディレクトリに保存しておく）
set_bg("background.png")

# タイトルとGmailボタンを横並びに表示
title_col, mail_col = st.columns([5, 1])

answer = ""  # 先に初期化

with title_col:
    st.title("🍳 料理チャットアプリ")
with mail_col:
    # 直近のAI回答（answer）があればGmailボタンを表示
    if answer:
        subject = "料理の材料と作り方"
        short_answer = answer[:1000]
        body = urllib.parse.quote(short_answer)
        gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to=&su={urllib.parse.quote(subject)}&body={body}"
        st.markdown(
            f'''
            <a href="{gmail_link}" target="_blank" style="
                display:inline-block;
                padding:8px 16px;
                font-size:16px;
                background:#1976d2;
                color:#fff;
                border:none;
                border-radius:6px;
                text-decoration:none;
                font-weight:bold;
                margin-top:24px;
            ">📧 Gmailで送る</a>
            ''',
            unsafe_allow_html=True
        )

# ここでスペースを追加
st.markdown("<br>", unsafe_allow_html=True)

st.write("料理に関する質問をどうぞ！")

# セキュリティのためst.secretsを利用
api_key = st.secrets["AZURE_OPENAI_API_KEY"]
endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"]
deployment_name = st.secrets["AZURE_OPENAI_DEPLOYMENT"]

# 新しいAzure OpenAIクライアントを作成
client = openai.AzureOpenAI(
    api_key=api_key,
    azure_endpoint=endpoint,
    api_version="2024-02-15-preview"
)

# メインとサイドの2カラムを作成
main_col, fav_col = st.columns([3, 2])

answer = ""  # グローバルで初期化

with main_col:
    cols = st.columns([2, 3, 1, 1, 1])  # 1番目のカラムを2倍、2番目を3倍の幅に

    with cols[0]:
        st.markdown(
            """
            <style>
            /* selectboxの親divに枠線を付ける */
            div[data-testid="stSelectbox"] {
                border: 2px solid #1976d2;
                border-radius: 8px;
                padding: 8px 4px;
                background: #fff;
                margin-bottom: 8px;
            }
            /* text inputの親divに枠線を付ける */
            div[data-testid="stTextInput"] {
                border: 2px solid #1976d2;
                border-radius: 8px;
                padding: 8px 4px;
                background: #fff;
                margin-bottom: 8px;
            }
            /* radioの親divに枠線を付ける */
            div[data-testid="stRadio"] {
                border: 2px solid #1976d2;
                border-radius: 8px;
                padding: 8px 4px;
                background: #fff;
                margin-bottom: 8px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        num_people = st.selectbox("何人分ですか？", [1, 2, 3, 4, 5], index=0)
    with cols[1]:
        difficulty = st.radio(
            "料理の難易度",
            ["簡単な料理", "ちょっと手間のかかる料理"],
            index=0,
            horizontal=True  # 横並びで分かりやすく
        )

    user_question = st.text_input("料理に関する質問を入力してください:", key="user_question")

    if user_question:
        with st.spinner("AIが考中..."):
            try:
                prompt = f"""{user_question}（{num_people}人分、{difficulty}で教えて。料理に合うお勧めのデザートや飲み物も提案してください）"""
                response = client.chat.completions.create(
                    model=deployment_name,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                answer = response.choices[0].message.content
                st.write(f"AIの回答: {answer}")

                # --- 星評価 ---
                st.subheader("このメニューの評価")
                rating = st.slider("星を付けて評価してください", 1, 5, 3, format="%d⭐")
                st.write(f"あなたの評価: {'⭐'*rating}")

                # --- お気に入り登録 ---
                if "favorites" not in st.session_state:
                    st.session_state.favorites = set()
                fav_key = f"fav_{answer[:30]}"

                if fav_key in st.session_state.favorites:
                    if st.button("★ お気に入り解除"):
                        st.session_state.favorites.remove(fav_key)
                        st.success("お気に入りから解除しました")
                    else:
                        st.info("お気に入り登録済み")
                else:
                    if st.button("☆ お気に入り登録"):
                        st.session_state.favorites.add(fav_key)
                        st.success("お気に入りに登録しました")

                # --- Gmail送信ボタン ---
                subject = "料理の材料と作り方"
                short_answer = answer[:1000]
                body = urllib.parse.quote(short_answer)
                gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to=&su={urllib.parse.quote(subject)}&body={body}"
                st.markdown(
                    f'''
                    <a href="{gmail_link}" target="_blank" style="
                        display:inline-block;
                        padding:8px 16px;
                        font-size:16px;
                        background:#1976d2;
                        color:#fff;
                        border:none;
                        border-radius:6px;
                        text-decoration:none;
                        font-weight:bold;
                        margin-top:24px;
                    ">📧 Gmailで送る</a>
                    ''',
                    unsafe_allow_html=True
                )

                # --- 材料費算出ボタン ---
                if st.button("💰 材料費を算出"):
                    st.subheader("🛒 材料費の詳細")
                    
                    # 材料リストを抽出（複数のパターンに対応）
                    ingredients = []
                    if answer:
                        # パターン1: 「材料」セクションから抽出
                        patterns = [
                            r"材料.*?\n((?:- .*\n)+)",           # - リスト形式
                            r"材料.*?\n((?:\d+\..*\n)+)",        # 1. 番号付きリスト
                            r"材料.*?\n((?:・.*\n)+)",           # ・ リスト形式
                            r"材料.*?[:：]\s*(.*?)(?:\n\n|\n作り方|\n手順|$)",  # : 以降の材料
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, answer, re.DOTALL | re.MULTILINE)
                            if match:
                                raw_ingredients = match.group(1).strip()
                                # 行ごとに分割して材料を抽出
                                for line in raw_ingredients.split('\n'):
                                    line = line.strip()
                                    if line and not line.startswith(('作り方', '手順', '調理法')):
                                        # 先頭の記号や番号を除去
                                        clean_line = re.sub(r'^[-・\d+\.\)]\s*', '', line)
                                        if clean_line:
                                            ingredients.append(clean_line)
                                break
                        
                        # パターンが見つからない場合、全体から食材らしきものを抽出
                        if not ingredients:
                            # 一般的な食材名を含む行を抽出
                            food_keywords = ['肉', '野菜', '魚', '米', '麺', '卵', '豆腐', '油', '醤油', '味噌', '塩', '砂糖', 
                                           '玉ねぎ', 'にんじん', 'じゃがいも', 'キャベツ', 'トマト', 'ピーマン']
                            
                            for line in answer.split('\n'):
                                line = line.strip()
                                if any(keyword in line for keyword in food_keywords):
                                    # 調理法や説明文を除外
                                    if not any(exclude in line for exclude in ['炒める', '煮る', '焼く', '切る', '作り方', '手順']):
                                        clean_line = re.sub(r'^[-・\d+\.\)]\s*', '', line)
                                        if clean_line and len(clean_line) < 50:  # 長すぎる行は除外
                                            ingredients.append(clean_line)
            
                    # デバッグ情報を表示
                    if not ingredients:
                        st.warning("材料の自動抽出に失敗しました。AI回答の形式を確認します...")
                        with st.expander("AI回答の内容を確認"):
                            st.text(answer)
                        st.info("手動で材料を入力することもできます。")
                        
                        # 手動入力オプション
                        manual_ingredients = st.text_area(
                            "材料を手動で入力してください（1行に1つずつ）:",
                            placeholder="例：\n玉ねぎ 1個\n豚肉 300g\n醤油 大さじ2"
                        )
                        if manual_ingredients:
                            ingredients = [line.strip() for line in manual_ingredients.split('\n') if line.strip()]
                    
                    # 材料の概算価格辞書（大幅拡張版）
                    price_dict = {
                        # 肉類
                        "豚肉": 400, "豚バラ": 450, "豚ロース": 500, "豚ひき肉": 350, "豚こま": 380,
                        "鶏肉": 300, "鶏もも": 350, "鶏むね": 250, "鶏ひき肉": 280, "手羽先": 320, "手羽元": 300,
                        "牛肉": 600, "牛バラ": 700, "牛ロース": 800, "牛ひき肉": 450, "牛切り落とし": 550,
                        "ベーコン": 400, "ハム": 350, "ソーセージ": 300, "ウインナー": 280,
                        
                        # 魚介類
                        "魚": 400, "鮭": 450, "サバ": 350, "アジ": 300, "イワシ": 250, "タラ": 400,
                        "エビ": 500, "イカ": 400, "タコ": 600, "ホタテ": 700, "カニ": 800,
                        "ツナ缶": 200, "さば缶": 180, "鮭缶": 220,
                        
                        # 野菜類
                        "玉ねぎ": 150, "にんじん": 120, "じゃがいも": 200, "キャベツ": 200, "トマト": 300,
                        "きゅうり": 150, "大根": 180, "白菜": 250, "ピーマン": 200, "パプリカ": 300,
                        "なす": 200, "ズッキーニ": 250, "かぼちゃ": 300, "ブロッコリー": 250, "カリフラワー": 280,
                        "ほうれん草": 200, "小松菜": 180, "チンゲン菜": 150, "レタス": 200, "サニーレタス": 180,
                        "もやし": 50, "豆苗": 100, "ネギ": 150, "長ネギ": 150, "万能ねぎ": 120,
                        "ニラ": 150, "生姜": 200, "にんにく": 180, "セロリ": 200, "アスパラ": 350,
                        "オクラ": 200, "いんげん": 250, "枝豆": 200, "とうもろこし": 300,
                        "れんこん": 300, "ごぼう": 250, "たけのこ": 400, "山芋": 350,
                        
                        # きのこ類
                        "しいたけ": 200, "えのき": 100, "しめじ": 150, "エリンギ": 180, "まいたけ": 200,
                        "マッシュルーム": 200, "なめこ": 150,
                        
                        # 豆類・豆腐製品
                        "豆腐": 100, "厚揚げ": 150, "油揚げ": 120, "絹ごし豆腐": 100, "木綿豆腐": 100,
                        "納豆": 150, "大豆": 200, "小豆": 250, "いんげん豆": 200,
                        
                        # 穀物・麺類
                        "米": 250, "白米": 250, "玄米": 300, "もち米": 280,
                        "パン": 150, "食パン": 120, "バゲット": 200, "ロールパン": 180,
                        "うどん": 120, "そば": 150, "そうめん": 100, "ラーメン": 120, "パスタ": 150,
                        "スパゲッティ": 150, "マカロニ": 120, "ペンネ": 150,
                        "小麦粉": 150, "片栗粉": 180, "パン粉": 120, "天ぷら粉": 200,
                        
                        # 卵・乳製品
                        "卵": 250, "たまご": 250, "うずらの卵": 300,
                        "牛乳": 200, "豆乳": 180, "生クリーム": 300, "ヨーグルト": 180,
                        "バター": 400, "マーガリン": 200, "クリームチーズ": 350,
                        "チーズ": 350, "モッツァレラ": 400, "パルメザン": 500, "チェダー": 380,
                        
                        # 調味料
                        "醤油": 200, "味噌": 300, "塩": 100, "砂糖": 180, "上白糖": 180, "三温糖": 200,
                        "酢": 200, "米酢": 220, "穀物酢": 180, "黒酢": 300,
                        "みりん": 250, "料理酒": 200, "日本酒": 400,
                        "ごま油": 350, "サラダ油": 300, "オリーブオイル": 500, "ココナッツオイル": 600,
                        "ケチャップ": 200, "マヨネーズ": 250, "ソース": 200, "ウスターソース": 200,
                        "コチュジャン": 300, "豆板醤": 250, "甜麺醤": 280, "オイスターソース": 250,
                        "ナンプラー": 300, "タバスコ": 400, "ラー油": 300,
                        
                        # 香辛料・ハーブ
                        "こしょう": 200, "黒胡椒": 220, "白胡椒": 250, "唐辛子": 200, "一味": 180,
                        "七味": 200, "わさび": 300, "からし": 150, "山椒": 400,
                        "カレー粉": 300, "ガラムマサラ": 400, "クミン": 350, "コリアンダー": 300,
                        "バジル": 200, "オレガノ": 250, "ローズマリー": 300, "タイム": 280,
                        "パセリ": 150, "大葉": 120, "しそ": 120,
                        
                        # だし・スープ
                        "だしの素": 200, "コンソメ": 180, "中華だし": 200, "鶏ガラスープ": 180,
                        "昆布": 300, "かつお節": 400, "煮干し": 250,
                        
                        # 缶詰・瓶詰
                        "トマト缶": 150, "コーン缶": 120, "ミックスビーンズ": 150,
                        "ジャム": 300, "はちみつ": 500, "メープルシロップ": 600,
                        
                        # 冷凍食品
                        "冷凍野菜": 200, "冷凍エビ": 600, "冷凍魚": 400, "冷凍肉": 500,
                        
                        # その他
                        "海苔": 300, "ごま": 200, "白ごま": 200, "黒ごま": 220,
                        "アーモンド": 400, "くるみ": 500, "ピーナッツ": 300,
                        "レーズン": 300, "ドライフルーツ": 400,
                        "春雨": 150, "わかめ": 200, "ひじき": 250, "昆布": 300,
                        "こんにゃく": 100, "しらたき": 120, "寒天": 200,
                        "パスタソース": 200, "カレールー": 180, "シチューの素": 200,
                    }
                    
                    total_cost = 0
                    
                    if ingredients:
                        st.success(f"材料を {len(ingredients)} 個検出しました:")
                        
                        # 材料費一覧表を作成
                        st.write("**材料別価格一覧表：**")
                        
                        # テーブル形式で表示
                        import pandas as pd
                        
                        table_data = []
                        for item in ingredients:
                            # 材料名から価格を推定（部分一致の精度向上）
                            estimated_price = 150  # デフォルト価格
                            matched_key = "その他"
                            
                            # より柔軟な価格マッチング
                            for key, price in price_dict.items():
                                if key in item or item in key:
                                    estimated_price = price
                                    matched_key = key
                                    break
                            
                            total_cost += estimated_price
                            
                            table_data.append({
                                "材料名": item,
                                "推定価格": f"¥{estimated_price}",
                                "マッチング": matched_key
                            })
                        
                        # DataFrameで表示
                        df = pd.DataFrame(table_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # 合計金額をハイライト表示
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #f0f8ff;
                                border: 2px solid #1976d2;
                                border-radius: 10px;
                                padding: 20px;
                                text-align: center;
                                margin: 20px 0;
                            ">
                                <h3 style="color: #1976d2; margin: 0;">
                                    💰 合計概算費用: ¥{total_cost:,}
                                </h3>
                                <p style="margin: 10px 0; color: #666;">
                                    ({num_people}人分)
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # 一人当たりの費用
                        per_person_cost = total_cost // num_people if num_people > 0 else total_cost
                        st.info(f"一人当たりの費用: 約¥{per_person_cost}")
                        
                        st.warning("※ 価格は概算です。実際の価格は各ショッピングサイトでご確認ください。")
                        
                    else:
                        st.error("材料リストが見つかりませんでした。AIの回答に材料が含まれていない可能性があります。")

            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")

with fav_col:
    st.subheader("🍽 食べられるお店を探す")
    menu_name = answer.split('\n')[0].replace("【", "").replace("】", "").replace("メニュー", "").strip() if answer else ""
    if menu_name:
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(menu_name + ' レストラン')}"
        tabelog_url = f"https://tabelog.com/rstLst/?vs=1&sa={urllib.parse.quote(menu_name)}"
        st.markdown(f"- [Googleで「{menu_name}」が食べられるお店を探す]({google_url})")
        st.markdown(f"- [食べログで「{menu_name}」のお店を探す]({tabelog_url})")
    else:
        st.write("メニューが決まると、お店検索リンクが表示されます。")

    st.subheader("🛒 ネットスーパーで材料を探す")
    ingredients = []
    if answer:
        match = re.search(r"材料.*?\n((?:- .*\n)+)", answer)
        if match:
            ingredients = [line.replace("- ", "").strip() for line in match.group(1).split("\n") if line.strip()]
    if ingredients:
        for item in ingredients:
            aeon_url = f"https://shop.aeon.com/netsuper/search/?keyword={urllib.parse.quote(item)}"
            seiyu_url = f"https://sm.rakuten.co.jp/search/?q={urllib.parse.quote(item)}"
            amazon_url = f"https://www.amazon.co.jp/s?k={urllib.parse.quote(item)}&i=grocery"
            st.markdown(
                f"- {item} [イオンで探す]({aeon_url}) / [西友で探す]({seiyu_url}) / [Amazonで探す]({amazon_url})"
            )
    else:
        st.write("メニューが決まると、材料のネットスーパー検索リンクが表示されます。")

# --- カロリー計算ボタン ---
if st.button("🔥 カロリーを計算"):
    st.subheader("📊 カロリー詳細")
    
    # 材料リストを抽出（材料費算出と同じロジック）
    ingredients = []
    if answer:
        # パターン1: 「材料」セクションから抽出
        patterns = [
            r"材料.*?\n((?:- .*\n)+)",           # - リスト形式
            r"材料.*?\n((?:\d+\..*\n)+)",        # 1. 番号付きリスト
            r"材料.*?\n((?:・.*\n)+)",           # ・ リスト形式
            r"材料.*?[:：]\s*(.*?)(?:\n\n|\n作り方|\n手順|$)",  # : 以降の材料
        ]
        
        for pattern in patterns:
            match = re.search(pattern, answer, re.DOTALL | re.MULTILINE)
            if match:
                raw_ingredients = match.group(1).strip()
                for line in raw_ingredients.split('\n'):
                    line = line.strip()
                    if line and not line.startswith(('作り方', '手順', '調理法')):
                        clean_line = re.sub(r'^[-・\d+\.\)]\s*', '', line)
                        if clean_line:
                            ingredients.append(clean_line)
                break
        
        # パターンが見つからない場合のフォールバック
        if not ingredients:
            food_keywords = ['肉', '野菜', '魚', '米', '麺', '卵', '豆腐', '油', '醤油', '味噌', '塩', '砂糖', 
                           '玉ねぎ', 'にんじん', 'じゃがいも', 'キャベツ', 'トマト', 'ピーマン']
            
            for line in answer.split('\n'):
                line = line.strip()
                if any(keyword in line for keyword in food_keywords):
                    if not any(exclude in line for exclude in ['炒める', '煮る', '焼く', '切る', '作り方', '手順']):
                        clean_line = re.sub(r'^[-・\d+\.\)]\s*', '', line)
                        if clean_line and len(clean_line) < 50:
                            ingredients.append(clean_line)

    # 材料の概算カロリー辞書（100gあたりのカロリー）
    calorie_dict = {
        # 肉類（100gあたり）
        "豚肉": 263, "豚バラ": 395, "豚ロース": 263, "豚ひき肉": 221, "豚こま": 250,
        "鶏肉": 200, "鶏もも": 253, "鶏むね": 191, "鶏ひき肉": 166, "手羽先": 211, "手羽元": 197,
        "牛肉": 259, "牛バラ": 517, "牛ロース": 318, "牛ひき肉": 224, "牛切り落とし": 259,
        "ベーコン": 405, "ハム": 196, "ソーセージ": 321, "ウインナー": 321,
        
        # 魚介類（100gあたり）
        "魚": 150, "鮭": 139, "サバ": 247, "アジ": 121, "イワシ": 217, "タラ": 77,
        "エビ": 82, "イカ": 88, "タコ": 76, "ホタテ": 72, "カニ": 65,
        "ツナ缶": 267, "さば缶": 190, "鮭缶": 155,
        
        # 野菜類（100gあたり）
        "玉ねぎ": 37, "にんじん": 36, "じゃがいも": 76, "キャベツ": 23, "トマト": 19,
        "きゅうり": 14, "大根": 18, "白菜": 14, "ピーマン": 22, "パプリカ": 30,
        "なす": 22, "ズッキーニ": 14, "かぼちゃ": 49, "ブロッコリー": 33, "カリフラワー": 27,
        "ほうれん草": 20, "小松菜": 14, "チンゲン菜": 9, "レタス": 12, "サニーレタス": 16,
        "もやし": 14, "豆苗": 31, "ネギ": 28, "長ネギ": 28, "万能ねぎ": 27,
        "ニラ": 21, "生姜": 30, "にんにく": 134, "セロリ": 15, "アスパラ": 22,
        
        # きのこ類（100gあたり）
        "しいたけ": 18, "えのき": 22, "しめじ": 18, "エリンギ": 24, "まいたけ": 16,
        "マッシュルーム": 11, "なめこ": 15,
        
        # 豆類・豆腐製品（100gあたり）
        "豆腐": 56, "厚揚げ": 150, "油揚げ": 386, "絹ごし豆腐": 56, "木綿豆腐": 72,
        "納豆": 200, "大豆": 417, "小豆": 339, "いんげん豆": 333,
        
        # 穀物・麺類（100gあたり）
        "米": 356, "白米": 356, "玄米": 350, "もち米": 359,
        "パン": 264, "食パン": 264, "バゲット": 279, "ロールパン": 316,
        "うどん": 105, "そば": 114, "そうめん": 127, "ラーメン": 149, "パスタ": 149,
        "スパゲッティ": 149, "マカロニ": 149, "ペンネ": 149,
        "小麦粉": 368, "片栗粉": 330, "パン粉": 373, "天ぷら粉": 349,
        
        # 卵・乳製品（100gあたり）
        "卵": 151, "たまご": 151, "うずらの卵": 179,
        "牛乳": 67, "豆乳": 46, "生クリーム": 433, "ヨーグルト": 62,
        "バター": 745, "マーガリン": 758, "クリームチーズ": 346,
        "チーズ": 339, "モッツァレラ": 276, "パルメザン": 475, "チェダー": 423,
        
        # 調味料（大さじ1あたり）
        "醤油": 13, "味噌": 35, "塩": 0, "砂糖": 35, "上白糖": 35, "三温糖": 34,
        "酢": 3, "米酢": 3, "穀物酢": 3, "黒酢": 5,
        "みりん": 43, "料理酒": 16, "日本酒": 16,
        "ごま油": 111, "サラダ油": 111, "オリーブオイル": 111, "ココナッツオイル": 111,
        "ケチャップ": 18, "マヨネーズ": 84, "ソース": 20, "ウスターソース": 20,
    }
    
    total_calories = 0
    
    if ingredients:
        st.success(f"材料を {len(ingredients)} 個検出しました:")
        
        # カロリー一覧表を作成
        st.write("**材料別カロリー一覧表：**")
        
        import pandas as pd
        
        table_data = []
        for item in ingredients:
            # 材料名からカロリーを推定
            estimated_calories = 50  # デフォルトカロリー
            matched_key = "その他"
            serving_note = "推定量"
            
            # より柔軟なカロリーマッチング
            for key, calories in calorie_dict.items():
                if key in item or item in key:
                    estimated_calories = calories
                    matched_key = key
                    # 調味料類は大さじ1、その他は100g基準
                    if key in ["醤油", "味噌", "酢", "みりん", "料理酒", "ケチャップ", "マヨネーズ", "ソース"]:
                        serving_note = "大さじ1"
                    elif key in ["ごま油", "サラダ油", "オリーブオイル"]:
                        serving_note = "大さじ1"
                    else:
                        serving_note = "100g"
                    break
            
            total_calories += estimated_calories
            
            table_data.append({
                "材料名": item,
                "カロリー": f"{estimated_calories}kcal",
                "基準量": serving_note,
                "マッチング": matched_key
            })
        
        # DataFrameで表示
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
        # 合計カロリーをハイライト表示
        st.markdown(
            f"""
            <div style="
                background-color: #fff3e0;
                border: 2px solid #ff9800;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                margin: 20px 0;
            ">
                <h3 style="color: #ff9800; margin: 0;">
                    🔥 合計概算カロリー: {total_calories:,}kcal
                </h3>
                <p style="margin: 10px 0; color: #666;">
                    ({num_people}人分)
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 一人当たりのカロリー
        per_person_calories = total_calories // num_people if num_people > 0 else total_calories
        st.info(f"一人当たりのカロリー: 約{per_person_calories}kcal")
        
        # カロリー評価
        if per_person_calories < 300:
            st.success("🌱 低カロリーな料理ですね！")
        elif per_person_calories < 600:
            st.info("⚖️ 適度なカロリーの料理です")
        else:
            st.warning("🔥 高カロリーな料理です。食べ過ぎに注意！")
        
        st.warning("※ カロリーは概算です。調理方法や分量により実際のカロリーは変動します。")
        
    else:
        st.error("材料リストが見つかりませんでした。AIの回答に材料が含まれていない可能性があります。")

st.markdown(
    """
    <style>
    /* 横幅を広げつつ、左右に適度な余白を作る */
    .block-container {
        max-width: 90vw !important;
        width: 90vw !important;
        padding-left: 5vw !important;
        padding-right: 5vw !important;
    }
    .stApp {
        padding: 0 !important;
        margin: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
