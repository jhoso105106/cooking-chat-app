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
            response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {
                        "role": "user",
                        "content": f"{user_question}（{num_people}人分、{difficulty}で教えて）"
                    }
                ]
            )
            answer = response.choices[0].message.content
            st.write(f"AIの回答: {answer}")

            # メール送信用 mailtoリンクを作成（URLエンコードを強化）
            subject = "料理の材料と作り方"
            body = urllib.parse.quote(answer)
            mailto_link = f"mailto:?subject={urllib.parse.quote(subject)}&body={body}"

            # ボタン風リンク（aタグのみで実装）
            st.markdown(
                f'''
                <a href="{mailto_link}" style="
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
                ">📧 メールで送る</a>
                ''',
                unsafe_allow_html=True
            )

        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
