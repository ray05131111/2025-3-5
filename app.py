from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import os
import base64
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

    # 讀取圖片並轉為 base64
    image_bytes = BytesIO(image_content.content)
    image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')

    print("✅ 圖片已轉換為 base64，準備傳送至 OpenAI", flush=True)

    client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一位國際象棋專家，請根據圖片分析棋局並給出建議。"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "請分析這張圖片的西洋棋局勢："},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"}
                ]
            }
        ]
    )

    reply_message = completion.choices[0].message.content

    print(f"📝 OpenAI 回覆：{reply_message}", flush=True)

    # 回覆使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )



if __name__ == "__main__":
    app.run(debug=True, port=8000)
