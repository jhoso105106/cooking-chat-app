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
                    
                    # 材料リストを抽出
                    ingredients = []
                    if answer:
                        match = re.search(r"材料.*?\n((?:- .*\n)+)", answer)
                        if match:
                            ingredients = [line.replace("- ", "").strip() for line in match.group(1).split("\n") if line.strip()]
                    
                    # 材料の概算価格辞書
                    price_dict = {
                        "玉ねぎ": 150,
                        "にんじん": 120,
                        "じゃがいも": 200,
                        "豚肉": 400,
                        "鶏肉": 300,
                        "牛肉": 600,
                        "米": 250,
                        "卵": 250,
                        "醤油": 200,
                        "味噌": 300,
                        "塩": 100,
                        "砂糖": 180,
                        "キャベツ": 200,
                        "トマト": 300,
                        "きゅうり": 150,
                        "大根": 180,
                        "白菜": 250,
                        "ピーマン": 200,
                        "もやし": 50,
                        "豆腐": 100,
                        "油": 300,
                        "バター": 400,
                        "牛乳": 200,
                        "チーズ": 350,
                        "パン": 150,
                        "麺": 120
                    }
                    
                    total_cost = 0
                    price_details = []
                    
                    if ingredients:
                        # 材料費一覧表を作成
                        st.write("**材料別価格一覧表：**")
                        
                        # テーブル形式で表示
                        import pandas as pd
                        
                        table_data = []
                        for item in ingredients:
                            # 材料名から価格を推定（部分一致）
                            estimated_price = 150  # デフォルト価格
                            matched_key = "その他"
                            
                            for key, price in price_dict.items():
                                if key in item:
                                    estimated_price = price
                                    matched_key = key
                                    break
                            
                            total_cost += estimated_price
                            
                            # 価格比較サイトのURL生成
                            search_url = f"https://kakaku.com/search_results/{urllib.parse.quote(item)}/"
                            
                            table_data.append({
                                "材料名": item,
                                "推定価格": f"¥{estimated_price}",
                                "参考": f"[価格を確認]({search_url})"
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
                        per_person_cost = total_cost // num_people
                        st.info(f"一人当たりの費用: 約¥{per_person_cost}")
                        
                        # 参考情報
                        st.subheader("📋 価格参考サイト")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("- [価格.com](https://kakaku.com/)")
                            st.markdown("- [楽天市場](https://www.rakuten.co.jp/)")
                        with col2:
                            st.markdown("- [Amazon](https://www.amazon.co.jp/)")
                            st.markdown("- [Yahoo!ショッピング](https://shopping.yahoo.co.jp/)")
                        with col3:
                            st.markdown("- [イオンネットスーパー](https://shop.aeon.com/netsuper/)")
                            st.markdown("- [楽天西友](https://sm.rakuten.co.jp/)")
                        
                        st.warning("※ 価格は概算です。実際の価格や在庫状況は各サイトでご確認ください。")
                        
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
