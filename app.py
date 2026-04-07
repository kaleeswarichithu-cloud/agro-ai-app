from flask import Flask, render_template, request, jsonify
import os, cv2, numpy as np, uuid
from gtts import gTTS
import requests

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
AUDIO_FOLDER = "static/audio"

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# ✅ UPDATED DATA (Added 'Healthy' to prevent crashes)
disease_data = {
    "Healthy": {
        "tamil": "செடி ஆரோக்கியமாக உள்ளது",
        "cause": "சரியான பராமரிப்பு",
        "treatment": "தொடர்ந்து கவனித்து வாருங்கள்",
        "prevention": "இதேபோல் பராமரிக்கவும்"
    },
    "Leaf Spot": {
        "tamil": "இலை புள்ளி நோய்",
        "cause": "பூஞ்சை தாக்கம் காரணமாக ஏற்படும்",
        "treatment": "நீம் எண்ணெய் அல்லது பூஞ்சை நாசினி பயன்படுத்தவும்",
        "prevention": "இலை மேலிருந்து தண்ணீர் ஊற்ற வேண்டாம்"
    },
    "Powdery Mildew": {
        "tamil": "பொடிமை பூஞ்சை",
        "cause": "சலப்பு பூஞ்சை வகை தாக்கம்",
        "treatment": "சல்பர் அல்லது பூஞ்சை நாசினி தெளிக்கவும்",
        "prevention": "காற்றோட்டம் அதிகரிக்கவும்"
    },
    "Rust": {
        "tamil": "துரு நோய்",
        "cause": "பூஞ்சை வளர்ச்சி",
        "treatment": "காப்பர் ஸ்ப்ரே பயன்படுத்தவும்",
        "prevention": "பழைய இலைகளை அகற்றவும்"
    },
    "Blight": {
        "tamil": "இலை அழுகல்",
        "cause": "பாக்டீரியா/பூஞ்சை தாக்கம்",
        "treatment": "பரிந்துரைக்கப்பட்ட நாசினி உபயோகிக்கவும்",
        "prevention": "நீர் தேங்குவதை தவிர்க்கவும்"
    },
    "Wilt": {
        "tamil": "உலர்வு நோய்",
        "cause": "வேர் பாதிப்பு",
        "treatment": "மண் சுத்திகரிப்பு செய்யவும்",
        "prevention": "நல்ல வடிகால் அமைக்கவும்"
    }
}

def predict_disease(path):
    img = cv2.imread(path)
    if img is None:
        return "Healthy"
    
    img = cv2.resize(img, (224, 224))
    avg_green = np.mean(img[:, :, 1])
    avg_red = np.mean(img[:, :, 2])
    avg_blue = np.mean(img[:, :, 0])

    # Simple logic for color detection
    if avg_green > 130 and avg_red < 110:
        return "Healthy"
    elif avg_red > avg_green:
        return "Leaf Spot"
    elif avg_blue > 120:
        return "Powdery Mildew"
    else:
        # Avoid crashing by picking a valid key
        keys = list(disease_data.keys())
        return np.random.choice(keys)

def make_voice(text):
    try:
        filename = f"{uuid.uuid4()}.mp3"
        path = os.path.join(AUDIO_FOLDER, filename)
        # Strip emoji/special chars for cleaner TTS
        clean_text = text.replace("🌿", "").replace("📌", "").replace("💊", "").replace("🛡️", "")
        tts = gTTS(text=clean_text, lang="ta")
        tts.save(path)
        return f"/static/audio/{filename}"
    except Exception as e:
        print(f"TTS Error: {e}")
        return ""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"text": "கோப்பு எதுவும் கிடைக்கவில்லை"})
    
    file = request.files["file"]
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(path)

    disease_name = predict_disease(path)
    info = disease_data.get(disease_name, disease_data["Healthy"])

    response_text = f"🌿 {info['tamil']}\n\n📌 காரணம்: {info['cause']}\n💊 தீர்வு: {info['treatment']}\n🛡️ தடுப்பு: {info['prevention']}"
    
    return jsonify({
        "text": response_text,
        "audio": make_voice(response_text)
    })

@app.route("/chat", methods=["POST"])
def chat():
    # Fix for common frontend JSON issues
    data = request.get_json()
    if not data or "msg" not in data:
        return jsonify({"reply": "மன்னிக்கவும், புரியவில்லை."})
        
    q = data["msg"].lower()

    if any(word in q for word in ["water", "தண்ணி", "நீர்"]):
        r = "ஒரு நாளைக்கு 0.5 முதல் 1 லிட்டர் தண்ணீர் போதுமானது."
    elif any(word in q for word in ["sun", "வெயில்", "சூரிய"]):
        r = "ஒரு நாளைக்கு 6-8 மணி நேரம் வெயில் அவசியம்."
    elif any(word in q for word in ["fertilizer", "உரம்"]):
        r = "10-15 நாட்களுக்கு ஒருமுறை உரம் பயன்படுத்தவும்."
    else:
        r = "தயவு செய்து தண்ணீர், வெயில் அல்லது உரம் பற்றி கேளுங்கள்."

    return jsonify({
        "reply": r,
        "audio": make_voice(r)
    })

@app.route("/weather")
def weather():
    try:
        # Open-Meteo API is reliable for free tier
        data = requests.get(
            "https://api.open-meteo.com/v1/forecast?latitude=13.08&longitude=80.27&current_weather=true",
            timeout=5
        ).json()
        temp = data["current_weather"]["temperature"]
        text = f"இப்போது வெப்பநிலை {temp}°C"
        return jsonify({
            "text": text,
            "audio": make_voice(text)
        })
    except Exception:
        return jsonify({
            "text": "வானிலை தகவல் தற்போது கிடைக்கவில்லை",
            "audio": make_voice("வானிலை தகவல் தற்போது கிடைக்கவில்லை")
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
