import os
import openai
import base64
import requests
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, ImageMessage, TextSendMessage

app = Flask(__name__)

# 設定 LINE Channel Access Token 和 Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_KEY = os.getenv("OPENAI_KEY")

print(f"🔹 OpenAI 版本: {openai.__version__}")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = openai.OpenAI(api_key=OPENAI_KEY)  # ✅ 修正 OpenAI 調用方式

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    line_handler.handle(body, request.headers["X-Line-Signature"])
    return "OK"
# 處理圖片訊息
@line_handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    try:
        message_id = event.message.id
        headers = {"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}
        url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
        response = requests.get(url, headers=headers)
    
        if response.status_code == 200:
            image_data = response.content
            image_base64 = base64.b64encode(image_data).decode("utf-8")
    
            # ✅ 修正 OpenAI API 請求
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "你是一個能分析圖片的 AI"},
                    {"role": "user", "content": "請分析這張圖片"},
                ],
                image={"base64": image_base64, "mime_type": "image/png"}  # ✅ 正確傳送 base64 圖片
            )
    
            reply_text = response.choices[0].message.content  # ✅ 確保使用新版的 API 回應格式
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 無法下載圖片"))
    except Exception as e:
        reply_text = f"❌ OpenAI API 錯誤: {str(e)}"
        print(reply_text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

