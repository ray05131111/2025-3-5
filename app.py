import tempfile
import os
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from openai import OpenAI

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 設定 LINE Channel Access Token 和 Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_KEY")

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
def handle_text_message(event):
    user_message = event.message.text

    client = OpenAI(api_key=OPENAI_API_KEY)

    completion = client.chat.completions.create(
        model="gpt-4",  # 使用 GPT-4 模型
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    reply_message = completion.choices[0].message.content

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

@line_handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    try:
        # 獲取圖片訊息的 ID
        message_id = event.message.id
        logger.info(f"Received image with message_id: {message_id}")

        # 從 LINE API 下載圖片內容
        image_content = line_bot_api.get_message_content(message_id)
        logger.info("Downloading image content...")

        # 使用 tempfile 創建臨時檔案來儲存圖片
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            for chunk in image_content.iter_content():
                temp_file.write(chunk)
            
            # 取得臨時檔案的路徑
            image_path = temp_file.name

        logger.info(f"Image saved to {image_path}")

        # 使用 OpenAI API 分析圖片
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        with open(image_path, "rb") as image_file:
            response = client.images.create(  # 使用 GPT-4 模型來處理圖片
                model="gpt-4",  # 使用 GPT-4 支援圖片分析
                image=image_file
            )

        logger.info(f"OpenAI response: {response}")

        # 假設 API 回應包含圖片的描述
        if 'data' in response and len(response['data']) > 0:
            reply_message = response['data'][0].get('description', 'No description available')
        else:
            reply_message = "Sorry, I couldn't process the image."

        logger.info(f"Reply message: {reply_message}")

        # 回傳圖片描述
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )

        # 清理臨時圖片檔案
        os.remove(image_path)
        logger.info("Temporary image file deleted")

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"Sorry, there was an error processing your image: {str(e)}")
        )

if __name__ == "__main__":
    app.run(port=8000)
