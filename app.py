from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import os
import base64
import requests
from io import BytesIO
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

# 取得圖片的 Base64 編碼
def get_image_base64(image_id):
    url = f"https://api-data.line.me/v2/bot/message/{image_id}/content"
    headers = {"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}  # 你的 LINE Channel Token
    response = requests.get(url)
    
    if response.status_code == 200:
        return base64.b64encode(response.content).decode("utf-8")
    else:
        print(f"❌ 無法下載圖片，錯誤碼: {response.status_code}")
        return None
        
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
    image_id = event.message.id  # 取得圖片 ID
    print(f"📷 收到圖片訊息，ID：{image_id}")

    # 取得圖片的 base64 編碼
    image_base64 = get_image_base64(image_id)
    
    if not image_base64:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 圖片處理失敗，請再試一次"))
        return
    
    print("✅ 圖片已轉換為 base64，準備傳送至 OpenAI")

    # 發送到 OpenAI API
    try:
        completion = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "你是一個國際象棋分析師"},
                {"role": "user", "content": [
                    {"type": "text", "text": "請幫我分析這個棋局"},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image_base64}}
                ]}
            ]
        )

        response_text = completion.choices[0].message.content
        print(f"📝 OpenAI 回覆：{response_text}")

        # 回應給 LINE 使用者
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))

    except Exception as e:
        print(f"❌ OpenAI API 錯誤：{e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ AI 分析失敗，請稍後再試"))


# 假設你有一個圖片上傳的函式，這個函式會把圖片上傳到你的伺服器或雲端儲存
def upload_image_to_service(image_bytes):
    # 此處是上傳圖片的示範代碼
    # 你需要根據你的服務來實現圖片上傳的邏輯，並回傳圖片 URL
    # 例如，假設你將圖片上傳到 AWS S3 或其他雲端儲存服務
    return "https://your-server.com/path/to/image.jpg"  # 回傳圖片 URL



if __name__ == "__main__":
    app.run(debug=True, port=8000)
