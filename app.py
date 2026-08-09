import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- BƯỚC 1: LẤY CÁC KEY TỪ BIẾN MÔI TRƯỜNG ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- BƯỚC 2: CẤU HÌNH AI & TÍNH CÁCH (Giữ nguyên như cũ) ---
genai.configure(api_key=GEMINI_API_KEY)

kien_thuc_nen = """
Bạn là Trợ lý Y tế thông minh của Trung tâm Y tế khu vực Diên Khánh (tỉnh Khánh Hòa).
[HÃY TỰ ĐIỀN ĐỊA CHỈ, GIỜ LÀM VIỆC VÀ QUY TẮC NHƯ BẠN ĐÃ LÀM Ở BƯỚC TRƯỚC VÀO ĐÂY NHÉ]
"""

model = genai.GenerativeModel(
    model_name='gemini-flash-latest',
    system_instruction=kien_thuc_nen
)

# --- BƯỚC 3: HÀM GỬI TIN NHẮN ---
def send_telegram_message(chat_id, text_content):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text_content, "parse_mode": "Markdown"})

def send_facebook_message(recipient_id, text_content):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text_content}
    }
    requests.post(url, json=payload)

# --- BƯỚC 4: XỬ LÝ NHẬN TIN NHẮN (TÁCH RIÊNG 2 NỀN TẢNG) ---

# 4A. Đường ống cho Telegram
@app.route('/telegram_webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    if data and "message" in data and "text" in data["message"]:
        user_msg = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]
        
        if user_msg.startswith('/start'):
            send_telegram_message(chat_id, "Xin chào! Mình là Trợ lý Y tế Diên Khánh trên Telegram.")
            return jsonify({"status": "success"}), 200

        try:
            ai_response = model.generate_content(user_msg)
            send_telegram_message(chat_id, ai_response.text)
        except Exception as e:
            send_telegram_message(chat_id, "Xin lỗi, hệ thống đang bận một chút.")
            
    return jsonify({"status": "success"}), 200

# 4B. Đường ống cho Facebook Messenger
@app.route('/facebook_webhook', methods=['GET', 'POST'])
def facebook_webhook():
    # Khi Facebook gửi yêu cầu xác minh (GET)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    # Khi có người nhắn tin trên Fanpage (POST)
    if request.method == 'POST':
        data = request.json
        if data.get('object') == 'page':
            for entry in data['entry']:
                for messaging_event in entry.get('messaging', []):
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message'].get('text')
                        
                        if message_text:
                            try:
                                ai_response = model.generate_content(message_text)
                                send_facebook_message(sender_id, ai_response.text)
                            except Exception as e:
                                send_facebook_message(sender_id, "Xin lỗi, hệ thống đang bận một chút.")
        return "EVENT_RECEIVED", 200

# --- BƯỚC 5: TRANG CHỦ & CÀI ĐẶT ---
@app.route('/', methods=['GET'])
def home():
    return "<h1>Hệ thống Bot đa nền tảng đang hoạt động!</h1>"

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    render_url = request.url_root.replace("http://", "https://") 
    webhook_url = f"{render_url}telegram_webhook"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"
    requests.get(url)
    return jsonify({"status": "Telegram Webhook updated"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
