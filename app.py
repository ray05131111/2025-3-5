import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from openai import OpenAI

# 使用環境變數儲存 API Key
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_SECRET = os.getenv("LINE_SECRET")
OPENAI_KEY = os.getenv("OPENAI_KEY")

# 初始化 LINE 和 OpenAI
line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
h = WebhookHandler(LINE_SECRET)
client = OpenAI(api_key=OPENAI_KEY)

# 啟動 Flask 伺服器
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot 運行中！"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        h.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# 🔹 **處理文字訊息**
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text  # 獲取使用者的文字訊息

    try:
        # 送到 OpenAI 取得回應
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_message}]
        )
        ai_response = response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 錯誤: {e}")
        ai_response = "抱歉，我現在無法回應，請稍後再試！"

    # 回覆使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_response)
    )

# 🔹 **處理圖片訊息**
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    image_id = event.message.id  # 取得圖片 ID
    image_content = line_bot_api.get_message_content(image_id)  # 下載圖片

    image_path = f"images/{image_id}.jpg"
    os.makedirs("images", exist_ok=True)  # 確保 images 資料夾存在

    # 儲存圖片
    with open(image_path, "wb") as f:
        for chunk in image_content.iter_content():
            f.write(chunk)

    print(f"圖片已儲存：{image_path}")

    try:
        # 使用 OpenAI GPT-4o 解析圖片
        with open(image_path, "rb") as f:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "請描述這張圖片的內容"},
                ],
                images=[f]  # 傳送圖片給 GPT-4o
            )

        ai_response = response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 錯誤: {e}")
        ai_response = "抱歉，我無法分析這張圖片。"

    # 回覆使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"圖片分析結果：{ai_response}")
    )

    print(f"AI 回覆：{ai_response}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
