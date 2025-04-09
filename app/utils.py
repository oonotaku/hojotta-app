import pdfplumber
import openai
from .config import OPENAI_API_KEY

# ✅ 新しいOpenAIクライアントを使う
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def extract_text_from_pdf(pdf_file_path):
    with pdfplumber.open(pdf_file_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    return text

def ask_gpt_about_requirements(text):
    prompt = f"""
あなたは補助金申請の専門家です。
以下の補助金の「要領」本文を読んで、申請時に必要なアウトプット（書類、作文、提出物など）を箇条書きで教えてください。

--- 要領本文（冒頭3,000文字） ---
{text[:3000]}
"""

    # ✅ 新バージョンのGPT呼び出し
    response = client.chat.completions.create(
        model="gpt-4-turbo",  # 必要に応じて gpt-3.5-turbo でもOK
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return response.choices[0].message.content
