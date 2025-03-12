from threading import Thread

def reply_async(reply_token, reply_message):
    try:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_message))
    except Exception as e:
        print(f"LINE API 回應錯誤: {e}")

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_token = event.reply_token
    
    # Webhook 立即回應 OK
    Thread(target=process_and_reply, args=(reply_token, user_message)).start()

def process_and_reply(reply_token, user_message):
    client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一個程式及數學高手"},
                {"role": "user", "content": user_message}
            ]
        )
        reply_message = completion.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 呼叫錯誤: {e}")
        reply_message = "抱歉，出現錯誤，請稍後再試。"

    reply_async(reply_token, reply_message)
