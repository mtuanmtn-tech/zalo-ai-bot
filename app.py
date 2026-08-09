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

# ĐỊNH HÌNH TÍNH CÁCH VÀ KIẾN THỨC CHO AI
kien_thuc_nen = """
Bạn là Trợ lý Y tế thông minh của Trung tâm Y tế khu vực Diên Khánh (tỉnh Khánh Hòa).
Nhiệm vụ của bạn là tư vấn sức khỏe cơ bản, hướng dẫn quy trình khám bệnh và cung cấp thông tin của Trung tâm.

Thông tin của Trung tâm (bạn phải luôn dựa vào đây để trả lời):
- Địa chỉ: Thôn Đông 1, xã Diên Điền, tỉnh Khánh Hòa
- Giờ làm việc: Sáng 7h00 - 11h30, Chiều 13h30 - 17h00 (Thứ 2 đến Thứ 6). Trực cấp cứu hoạt động 24/7.
- Số điện thoại liên hệ: 0965241515

Quy tắc giao tiếp bắt buộc:
1. Luôn xưng hô là "Trợ lý Y tế Trung tâm Y tế khu vực Diên Khánh" và gọi người dùng là "bạn", "anh/chị" hoặc "quý bệnh nhân". Thái độ luôn ân cần, đồng cảm và chuyên nghiệp.
2. Với các câu hỏi về triệu chứng bệnh: Hãy tư vấn thông tin y khoa cơ bản, NHƯNG cuối câu luôn phải có lời khuyên: "Thông tin này chỉ mang tính tham khảo. Để an toàn nhất, bạn nên đến trực tiếp Trung tâm Y tế khu vực Diên Khánh để được các bác sĩ thăm khám và chẩn đoán chính xác."
3. Tuyệt đối không được kê đơn thuốc cụ thể (không đọc tên thuốc kháng sinh, thuốc đặc trị) dưới bất kỳ hình thức nào.
"""

model = genai.GenerativeModel(
    model_name='gemini-flash-latest',
    system_instruction=kien_thuc_nen
)

# --- BƯỚC 3: HÀM GỬI TIN NHẮN LẠI TELEGRAM ---
def send_telegram_message(chat_id, text_content):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text_content,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)
    return {"status": "ok"}

# --- BƯỚC 4: NHẬN WEBHOOK TỪ TELEGRAM ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    if data and "message" in data and "text" in data["message"]:
        user_msg = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]
        
        if user_msg.startswith('/'):
            if user_msg == '/start':
                send_telegram_message(chat_id, "Xin chào! Mình là Trợ lý Y tế khu vực Diên Khánh. Mình có thể giúp gì cho quý bệnh nhân?")
            return jsonify({"status": "success"}), 200

        try:
            ai_response = model.generate_content(user_msg)
            send_telegram_message(chat_id, ai_response.text)
            
        except Exception as e:
            print("Lỗi:", e)
            send_telegram_message(chat_id, "Xin lỗi, hệ thống đang bận một chút. Vui lòng thử lại sau ạ.")
            
    return jsonify({"status": "success"}), 200

# --- BƯỚC 5 & 6: TRANG CHỦ & CÀI ĐẶT WEBHOOK ---
@app.route('/', methods=['GET'])
def home():
    return "Telegram AI Bot đang hoạt động tốt!"

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    render_url = request.url_root.replace("http://", "https://") 
    webhook_url = f"{render_url}webhook"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"
    requests.get(url)
    return jsonify({"status": "Webhook updated"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
