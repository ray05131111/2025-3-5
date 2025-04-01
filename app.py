import os
import tempfile
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from google.cloud import vision

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 設定 LINE Channel Access Token 和 Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_KEY")

# 設定 Google Cloud 憑證金鑰
google_credentials_json = os.getenv("GOOGLE_CREDENTIALS")
if google_credentials_json:
    with open("gcp_credentials.json", "w") as temp_cred:
        temp_cred.write(google_credentials_json)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

# 建立 Vision API 客戶端
client = vision.ImageAnnotatorClient()

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
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": user_message}]
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

        # 使用 Google Vision API 進行圖片分析
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        # 建立 Image 物件並設置內容
        image = vision.Image()
        image.content = content

        # 使用 label_detection 來進行圖片標籤識別
        response = client.label_detection(image=image)

        # 檢查 API 回應錯誤
        if response.error.message:
            logger.error(f"Google Vision API Error: {response.error.message}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Sorry, there was an error with the image analysis.")
            )
            return

        # 取得圖片的標籤
        labels = response.label_annotations
        if labels:
            reply_message = "I found these labels in the image:\n" + "\n".join([label.description for label in labels])
        else:
            reply_message = "No labels found in the image."

        logger.info(f"Reply message: {reply_message}")

        # 回傳圖片分析結果
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
