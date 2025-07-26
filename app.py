import streamlit as st
import openai
import base64
import os
import urllib.parse


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
        display: inline-block;
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

st.title("🍳 料理チャットアプリ")
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

with main_col:
    cols = st.columns([2, 3, 1, 1, 1])  # 1番目のカラムを2倍、2番目を3倍の幅に

    with cols[0]:
        num_people = st.selectbox("何人分ですか？", [1, 2, 3, 4, 5], index=0)
    with cols[1]:
        difficulty = st.radio(
            "料理の難易度",
            ["簡単な料理", "ちょっと手間のかかる料理"],
            index=0,
            horizontal=True  # 横並びで表示
        )

    user_question = st.text_input("料理に関する質問を入力してください:")

    if user_question:
        with st.spinner("AIが考え中..."):
            try:
                # デザートや飲み物もおすすめするように指示を追加
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
                fav_key = f"fav_{answer[:30]}"  # 回答の先頭30文字でユニークキー

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

                # --- Gmail送信ボタン（そのまま） ---
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
                        margin-top:10px;
                    ">📧 Gmailで送る</a>
                    ''',
                    unsafe_allow_html=True
                )

            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")

with fav_col:
    st.subheader("⭐ お気に入りリスト")
    if "favorites" in st.session_state and st.session_state.favorites:
        for fav in st.session_state.favorites:
            st.markdown(f"- {fav}")
    else:
        st.write("お気に入りはまだありません。")

st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 100vw !important;
        width: 100vw !important;
        padding-left: 0vw !important;
        padding-right: 0vw !important;
    }
    .stApp {
        padding: 0 !important;
        margin: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
