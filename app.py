import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- BƯỚC 1: LẤY CÁC KEY TỪ BIẾN MÔI TRƯỜNG ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- BƯỚC 2: CẤU HÌNH GOOGLE GEMINI AI ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# --- BƯỚC 3: HÀM GỬI TIN NHẮN LẠI TELEGRAM ---
def send_telegram_message(chat_id, text_content):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text_content,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    print("Kết quả gửi Telegram:", response.json())
    return response.json()

# --- BƯỚC 4: NHẬN WEBHOOK TỪ TELEGRAM ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Nhận dữ liệu từ Telegram:", data)
    
    # Telegram lưu tin nhắn trong cấu trúc 'message' -> 'text'
    if data and "message" in data and "text" in data["message"]:
        user_msg = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]
        
        # Bỏ qua các lệnh hệ thống (như /start)
        if user_msg.startswith('/'):
            if user_msg == '/start':
                send_telegram_message(chat_id, "Xin chào! Mình là trợ lý AI y tế. Mình có thể giúp gì cho bạn?")
            return jsonify({"status": "success"}), 200

        try:
            # Gọi Gemini suy nghĩ câu trả lời
            ai_response = model.generate_content(user_msg)
            reply_text = ai_response.text
            send_telegram_message(chat_id, reply_text)
            
        except Exception as e:
            print("Lỗi khi xử lý AI:", e)
            send_telegram_message(chat_id, "Xin lỗi, hệ thống AI đang bận một chút. Vui lòng thử lại sau ạ.")
            
    return jsonify({"status": "success"}), 200

# --- BƯỚC 5: TRANG CHỦ ---
@app.route('/', methods=['GET'])
def home():
    return "<h1>Telegram AI Bot đang hoạt động tốt!</h1>"

# --- BƯỚC 6: TỰ ĐỘNG CÀI ĐẶT WEBHOOK CHO TELEGRAM (RẤT TIỆN LỢI) ---
@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    # Tự động lấy URL của Render để báo cho Telegram
    render_url = request.url_root.replace("http://", "https://") 
    webhook_url = f"{render_url}webhook"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"
    response = requests.get(url)
    return jsonify({"webhook_url_setup": webhook_url, "telegram_response": response.json()})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
