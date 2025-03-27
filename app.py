from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import os
from openai import OpenAI
from flask import send_from_directory

app = Flask(__name__)

# 設定 LINE Channel Access Token 和 Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_KEY = os.getenv("OPENAI_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_KEY)

@app.route('/')
def home():
    return "LINE BOT 正在運行"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    
    print(f"📩 收到 LINE Webhook 請求：{body}")  # Debug 訊息
    
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# 處理文字訊息（西洋棋建議）
@line_handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a chess expert who provides strategic advice."},
                {"role": "user", "content": user_message}
            ]
        )
        reply_message = completion.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 錯誤: {e}")
        reply_message = "抱歉，我目前無法提供西洋棋建議，請稍後再試。"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

@app.route('/favicon.png')
def favicon():
    return send_from_directory('static', 'favicon.png', mimetype='image/png')

# 處理圖片訊息（棋局分析）
@line_handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    print(f"📷 收到圖片訊息，ID：{event.message.id}", flush=True)  # 這行應該會在 log 中出現

    image_id = event.message.id  # 取得圖片 ID
    image_content = line_bot_api.get_message_content(image_id)  # 下載圖片

    image_path = f"images/{image_id}.jpg"
    os.makedirs("images", exist_ok=True)  # 確保 images 資料夾存在

    # 儲存圖片
    with open(image_path, "wb") as f:
        for chunk in image_content.iter_content():
            f.write(chunk)

    print(f"✅ 圖片已儲存至 {image_path}", flush=True)
    
    try:
        with open(image_path, "rb") as f:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "你是西洋棋特級大師，根據圖片或訊息用繁體中文給予建議"}
                ],
                images=[f]  # 傳送圖片給 GPT-4o 進行分析
            )
        ai_response = response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 錯誤: {e}")
        ai_response = "抱歉，我無法分析這張棋局圖片。"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"棋局分析結果：{ai_response}")
    )

if __name__ == "__main__":
    app.run(debug=True, port=8000)
