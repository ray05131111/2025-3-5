import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI

app = Flask(__name__)

# 取得環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_SECRET")
OPENAI_KEY = os.getenv("OPENAI_KEY")

# 檢查環境變數是否設定
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET or not OPENAI_KEY:
    raise ValueError("請確認環境變數 LINE_ACCESS_TOKEN、LINE_SECRET 和 OPENAI_KEY 是否設定！")

# 初始化 LINE Bot 和 OpenAI
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(LINE_CHANNEL_SECRET)  # ✅ 修正變數名稱
client = OpenAI(api_key=OPENAI_KEY)

@app.route('/')
def home():
    return "LINE BOT 運行中"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        line_handler.handle(body, signature)  # ✅ 使用正確的變數名稱
    except InvalidSignatureError:
        abort(400)

    return "OK"

@line_handler.add(MessageEvent, message=TextMessage)  # ✅ 修正變數名稱
def handle_message(event):
    user_message = event.message.text

    try:
        # 取得 OpenAI 回應
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        reply_message = completion.choices[0].message.content

        # 回覆訊息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )
    except Exception as e:
        print(f"OpenAI API 錯誤: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="抱歉，發生錯誤，請稍後再試。")
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # ✅ 確保 PORT 設定正確
    app.run(host="0.0.0.0", port=port, debug=True)
