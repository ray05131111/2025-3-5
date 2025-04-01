# import os
# import tempfile
# import logging
# from flask import Flask, request, abort
# from linebot import LineBotApi, WebhookHandler
# from linebot.exceptions import InvalidSignatureError
# from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage

# # 設定日誌
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = Flask(__name__)

# # 設定 LINE Channel Access Token 和 Secret
# LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
# LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
# line_handler = WebhookHandler(LINE_CHANNEL_SECRET)

# @app.route('/')
# def home():
#     return "LINE BOT 首頁"

# @app.route("/callback", methods=["POST"])
# def callback():
#     signature = request.headers["X-Line-Signature"]
#     body = request.get_data(as_text=True)

#     try:
#         line_handler.handle(body, signature)
#     except InvalidSignatureError:
#         abort(400)

#     return "OK"

# @line_handler.add(MessageEvent, message=ImageMessage)
# def handle_image_message(event):
#     try:
#         # 取得圖片訊息的 ID
#         message_id = event.message.id
#         logger.info(f"Received image with message_id: {message_id}")

#         # 從 LINE API 下載圖片內容
#         image_content = line_bot_api.get_message_content(message_id)
#         logger.info("Downloading image content...")

#         # 儲存圖片為臨時檔案
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
#             for chunk in image_content.iter_content():
#                 temp_file.write(chunk)
            
#             # 取得臨時檔案的路徑
#             image_path = temp_file.name

#         logger.info(f"Image saved to {image_path}")

#         # 回覆圖片已經成功接收
#         reply_message = "圖片已成功接收！"

#         line_bot_api.reply_message(
#             event.reply_token,
#             TextSendMessage(text=reply_message)
#         )

#         # 清理臨時檔案
#         os.remove(image_path)
#         logger.info("Temporary image file deleted")

#     except Exception as e:
#         logger.error(f"Error processing image: {e}")
#         line_bot_api.reply_message(
#             event.reply_token,
#             TextSendMessage(text="抱歉，處理圖片時發生錯誤。")
#         )

# if __name__ == "__main__":
#     app.run(port=8000)
