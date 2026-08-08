import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- BƯỚC 1: LẤY CÁC KEY TỪ BIẾN MÔI TRƯỜNG ---
ZALO_ACCESS_TOKEN = os.environ.get("ZALO_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- BƯỚC 2: CẤU HÌNH GOOGLE GEMINI AI ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- BƯỚC 3: HÀM GỬI TIN NHẮN LẠI ZALO ---
def send_zalo_message(user_id, text_content):
    url = "https://openapi.zalo.me/v3.0/oa/message/cs"
    
    headers = {
        "Content-Type": "application/json",
        "access_token": ZALO_ACCESS_TOKEN
    }
    
    payload = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": text_content
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# --- BƯỚC 4: NHẬN WEBHOOK TỪ ZALO ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Nhận dữ liệu từ Zalo:", data)
    
    if data and data.get("event_name") == "user_send_text":
        user_msg = data.get("message", {}).get("text", "")
        user_id = data.get("sender", {}).get("id")
        
        if user_msg and user_id:
            try:
                ai_response = model.generate_content(user_msg)
                reply_text = ai_response.text
                send_zalo_message(user_id, reply_text)
                
            except Exception as e:
                print("Lỗi khi xử lý AI:", e)
                send_zalo_message(user_id, "Xin lỗi bác sĩ, hệ thống AI đang bận một chút. Vui lòng thử lại sau ạ.")
                
    return jsonify({"status": "success"}), 200

# --- BƯỚC 5: TRANG CHỦ & XÁC THỰC DOMAIN ZALO ---
@app.route('/', methods=['GET'])
def home():
    return """
    <html>
        <head>
            <meta name="zalo-platform-site-verification" content="Ck6WCzRIBWHSu8yhcEm_2cp6kZM0i61kDJKr" />
        </head>
        <body>
            <h1>Zalo AI Bot đang hoạt động tốt!</h1>
        </body>
    </html>
    """

# --- BƯỚC 6: CÔNG CỤ KIỂM TRA MODEL AI ---
@app.route('/check', methods=['GET'])
def check_models():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return jsonify({"available_models": models})
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
