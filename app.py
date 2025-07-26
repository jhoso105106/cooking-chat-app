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
        num_people = st.selectbox("何人分ですか？", [1, 2, 3, 4, 5], index=0)
    with cols[1]:
        difficulty = st.radio(
            "料理の難易度",
            ["簡単な料理", "ちょっと手間のかかる料理"],
            index=0,
            horizontal=True  # 横並びにする
        )

    user_question = st.text_input("料理に関する質問を入力してください:")

    if user_question:
        with st.spinner("AIが考え中..."):
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

                # --- Gmail送信ボタン（タイトル横ではなく、ここに表示） ---
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
