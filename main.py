from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    ImageSendMessage)
from assistant_chat import *
import re
import os
from openai import OpenAI

client = OpenAI()

api = LineBotApi(os.getenv('LINE_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_SECRET'))

app = Flask(__name__)

@app.post("/")
def callback():
    # 取得 X-Line-Signature 表頭電子簽章內容
    signature = request.headers['X-Line-Signature']

    # 以文字形式取得請求內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 比對電子簽章並處理請求內容
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("電子簽章錯誤, 請檢查密鑰是否正確？")
        abort(400)

    return 'OK'

#處理 Assistant 和 Thread 的識別碼
ass_id, thread_id = get_thread_assistant_ids()

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text
    assistant_output = chat_with_functions(
        user_input, 
        ass_id, 
        thread_id
    )

    #使用規則表達式來尋找網址
    urls = re.findall(r'https?://[^\s)\]]+', assistant_output)
    #確認urls是否有圖片網址，以便進一步決定輸出的方式。
    if urls:  #如果urls中包含元素，則執行if陳述句
        print(f'使用者:{user_input}')
        print('發現圖片：')
        print(urls[0])
        api.reply_message(
            event.reply_token,
            ImageSendMessage(original_content_url=urls[0],
                             preview_image_url=urls[0]))
    else:
        print(f'使用者:{user_input}\n'
              f'AI:{assistant_output}')
        api.reply_message(event.reply_token, 
                          TextSendMessage(text=assistant_output))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)