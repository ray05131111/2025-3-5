from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import openai
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# 設定 LINE Channel Access Token 和 Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_KEY = os.getenv("OPENAI_KEY")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("請設置 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET 環境變數")

if not OPENAI_KEY:
    raise ValueError("請設置 OPENAI_KEY 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route('/')
def home():
    return "LINE BOT 首頁"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")

    body = request.get_data(as_text=True)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        print(f"處理訊息時發生錯誤: {e}")
        abort(500)

    return "OK"

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    openai.api_key = OPENAI_KEY

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # 使用有效的 OpenAI 模型
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        )

        reply_message = response["choices"][0]["message"]["content"]

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )
    except Exception as e:
        print(f"OpenAI API 錯誤: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="抱歉，我無法回應您的問題，請稍後再試。")
        )

if __name__ == "__main__":
    app.run(port=8000)
