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
        client = vision.ImageAnnotatorClient()

        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = client.label_detection(image=image)

        # **新增這行來檢查 API 回應**
        logger.info(f"Vision API Response: {response}")
        print(response)  # 如果在本地運行，這行會顯示完整的 API 回應

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
