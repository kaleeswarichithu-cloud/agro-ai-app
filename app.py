from flask import Flask, render_template, request, jsonify
import os, cv2, numpy as np, uuid
from gtts import gTTS
import requests

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = "static/uploads"
AUDIO_FOLDER = "static/audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# ✅ Disease Data (Includes 'Healthy' to prevent crashes)
disease_data = {
    "Healthy": {
        "tamil": "செடி ஆரோக்கியமாக உள்ளது",
        "cause": "சரியான பராமரிப்பு மற்றும் நீர் மேலாண்மை.",
        "treatment": "இதேபோல் தொடர்ந்து பராமரிக்கவும்.",
        "prevention": "வழக்கமான கண்காணிப்பு அவசியம்."
    },
    "Leaf Spot": {
        "tamil": "இலை புள்ளி நோய்",
        "cause": "பூஞ்சை தாக்கம் காரணமாக ஏற்படும்.",
        "treatment": "நீம் எண்ணெய் அல்லது பூஞ்சை நாசினி பயன்படுத்தவும்.",
        "prevention": "இலைகளின் மேல் நேரடியாகத் தண்ணீர் ஊற்றுவதைத் தவிர்க்கவும்."
    },
    "Powdery Mildew": {
        "tamil": "சாம்பல் நோய்",
        "cause": "ஈரப்பதம் மற்றும் பூஞ்சை தொற்று.",
        "treatment": "சல்பர் கலந்த நாசினியைத் தெளிக்கவும்.",
        "prevention": "செடிகளுக்கு இடையே போதிய காற்றோட்டத்தை உறுதி செய்யவும்."
    },
    "Blight": {
        "tamil": "இலை கருகல் நோய்",
        "cause": "பாக்டீரியா அல்லது பூஞ்சை தொற்று.",
        "treatment": "பாதிக்கப்பட்ட இலைகளை அகற்றிவிட்டு நாசினி தெளிக்கவும்.",
        "prevention": "மண்ணில் நீர் தேங்காமல் பார்த்துக் கொள்ளவும்."
    }
}

def predict_disease(path):
    img = cv2.imread(path)
    if img is None: return "Healthy"
    img = cv2.resize(img, (224, 224))
    avg_green = np.mean(img[:, :, 1])
    avg_red = np.mean(img[:, :, 2])
    
    # Simple Logic: If red tones outweigh green, it's likely a spot/blight
    if avg_green > 130 and avg_red < 110:
        return "Healthy"
    elif avg_red > avg_green:
        return "Leaf Spot"
    else:
        return "Blight"

def make_voice(text):
    try:
        filename = f"{uuid.uuid4()}.mp3"
        path = os.path.join(AUDIO_FOLDER, filename)
        # Remove emojis for cleaner TTS
        clean_text = text.replace("🌿", "").replace("📌", "").replace("💊", "").replace("🛡️", "")
        tts = gTTS(text=clean_text, lang="ta")
        tts.save(path)
        return f"/static/audio/{filename}"
    except:
        return ""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    if 'file' not in request.files:
        return jsonify({"text": "கோப்பு கிடைக்கவில்லை"})
    file = request.files['file']
    path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{file.filename}")
    file.save(path)
    
    result_key = predict_disease(path)
    info = disease_data.get(result_key, disease_data["Healthy"])
    
    response_text = f"🌿 {info['tamil']}\n\n📌 காரணம்: {info['cause']}\n💊 தீர்வு: {info['treatment']}\n🛡️ தடுப்பு: {info['prevention']}"
    return jsonify({"text": response_text, "audio": make_voice(response_text)})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    q = data.get("msg", "").lower()
    
    if any(word in q for word in ["water", "தண்ணி", "நீர்"]):
        r = "செடிகளுக்கு அதிகாலை அல்லது மாலையில் நீர் ஊற்றுவது சிறந்தது."
    elif any(word in q for word in ["sun", "வெயில்", "ஒளி"]):
        r = "பெரும்பாலான செடிகளுக்கு தினமும் 6 மணிநேர சூரிய ஒளி தேவை."
    elif any(word in q for word in ["fertilizer", "உரம்"]):
        r = "இயற்கை உரங்களான தொழு உரம் அல்லது மண்புழு உரம் பயன்படுத்தவும்."
    else:
        r = "மன்னிக்கவும், என்னால் நீர், வெயில் மற்றும் உரம் பற்றி மட்டுமே பதிலளிக்க முடியும்."
        
    return jsonify({"reply": r, "audio": make_voice(r)})

@app.route("/weather")
def weather():
    try:
        res = requests.get("https://api.open-meteo.com/v1/forecast?latitude=13.08&longitude=80.27&current_weather=true").json()
        temp = res["current_weather"]["temperature"]
        text = f"தற்போதைய வெப்பநிலை {temp}°C"
        return jsonify({"text": text, "audio": make_voice(text)})
    except:
        return jsonify({"text": "வானிலை தகவல் கிடைக்கவில்லை", "audio": ""})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
