import streamlit as st
import openai
import base64
import os


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

openai.api_type = "azure"
openai.api_key = api_key
openai.api_base = endpoint
openai.api_version = "2024-02-15-preview"

user_question = st.text_input("料理に関する質問を入力してください:")
if user_question:
    with st.spinner("AIが考え中..."):
        try:
            response = openai.ChatCompletion.create(
                deployment_id=deployment_name,
                messages=[
                    {"role": "user", "content": user_question}
                ]
            )
            st.write(f"AIの回答: {response['choices'][0]['message']['content']}")
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
