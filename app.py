from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import os
from openai import OpenAI
import requests

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
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message}
        ]
    )
    
    reply_message = completion.choices[0].message.content
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

@line_handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id)
    image_path = f"temp_{message_id}.jpg"
    
    with open(image_path, "wb") as f:
        for chunk in image_content.iter_content():
            f.write(chunk)
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    with open(image_path, "rb") as image_file:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an image analysis assistant."},
                {"role": "user", "content": "Describe this image in detail."},
                {"role": "user", "image": image_file.read()}
            ]
        )
    
    reply_message = response.choices[0].message.content
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

    os.remove(image_path)  # 清理暫存圖片

if __name__ == "__main__":
    app.run(port=8000)
