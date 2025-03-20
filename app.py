from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from openai import OpenAI

app = Flask(__name__)

# 設定 LINE Channel Access Token 和 Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(LINE_CHANNEL_SECRET)
@app.route('/')
def home():
    return "LINE BOT 首頁"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是西洋棋特級大師，能夠從圖片判斷西洋棋局勢並給出建議"},
                {"role": "user", "content": user_message}
            ]
        )
        reply_message = completion.choices[0].message.content
        print(f"OpenAI 回應: {reply_message}")  # 查看 OpenAI 回應
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )
    except Exception as e:
        print(f"OpenAI API 呼叫錯誤: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="抱歉，出現錯誤，請稍後再試。")
        )

    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )
# 處理圖片訊息
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    image_id = event.message.id  # 獲取圖片 ID
    image_content = line_bot_api.get_message_content(image_id)  # 下載圖片

    image_path = f"images/{image_id}.jpg"
    os.makedirs("images", exist_ok=True)  # 確保 images 資料夾存在

    # 儲存圖片
    with open(image_path, "wb") as f:
        for chunk in image_content.iter_content():
            f.write(chunk)

    print(f"圖片已儲存：{image_path}")

    # 使用 OpenAI GPT-4o 解析圖片
    with open(image_path, "rb") as f:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一個聰明的 AI 助理，請根據圖片內容給出簡單的描述"},
            ],
            images=[f]  # 傳送圖片給 GPT-4o
        )

    # 取得 AI 解析的結果
    ai_response = response.choices[0].message.content

    # 回覆使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"我看到的內容是：{ai_response}")
    )

    print(f"AI 回覆：{ai_response}")

if __name__ == "__main__":
    app.run(port=8000)
