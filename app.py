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
    print(f"📷 收到圖片訊息，ID：{event.message.id}", flush=True)  # 確保有進入函式

    # 取得圖片內容
    image_id = event.message.id
    image_content = line_bot_api.get_message_content(image_id)

    # 下載圖片到本地（或者上傳至服務）
    image_bytes = BytesIO(image_content.content)

    # 上傳圖片至可公開存取的伺服器（這裡假設上傳到你的服務）
    image_url = upload_image_to_service(image_bytes)

    print(f"✅ 圖片已上傳，URL: {image_url}", flush=True)

    # 生成圖片描述或其他相關訊息，這裡的消息是基於圖片的描述
    user_message = f"請分析這張圖片的西洋棋局勢。圖片連結：{image_url}"

    client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

    try:
        # 用 OpenAI 的圖片生成模型來處理圖片的 URL，並獲取結果
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一位國際象棋專家，請根據圖片連結分析棋局並給出建議。"},
                {"role": "user", "content": user_message}
            ]
        )

        reply_message = completion.choices[0].message.content
        print(f"📝 OpenAI 回覆：{reply_message}", flush=True)

        # 回覆使用者
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )
    except Exception as e:
        print(f"🚨 OpenAI 請求錯誤: {e}", flush=True)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="無法處理圖片，請稍後再試。")
        )

# 假設你有一個圖片上傳的函式，這個函式會把圖片上傳到你的伺服器或雲端儲存
def upload_image_to_service(image_bytes):
    # 此處是上傳圖片的示範代碼
    # 你需要根據你的服務來實現圖片上傳的邏輯，並回傳圖片 URL
    # 例如，假設你將圖片上傳到 AWS S3 或其他雲端儲存服務
    return "https://your-server.com/path/to/image.jpg"  # 回傳圖片 URL



if __name__ == "__main__":
    app.run(debug=True, port=8000)
