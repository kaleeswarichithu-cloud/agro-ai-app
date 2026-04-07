from flask import Flask, render_template, request, jsonify
import os, cv2, numpy as np, uuid
from gtts import gTTS
import requests

app = Flask(__name__, static_folder="static", template_folder="templates")

UPLOAD_FOLDER = "static/uploads"
AUDIO_FOLDER = "static/audio"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

disease_data = {
    "Leaf Spot": {
        "tamil": "இலை புள்ளி நோய்",
        "cause": "பூஞ்சை தாக்கம் காரணமாக ஏற்படும்",
        "treatment": "நீம் எண்ணெய் பயன்படுத்தவும்",
        "prevention": "மேலிருந்து தண்ணீர் ஊற்ற வேண்டாம்"
    },
    "Healthy": {
        "tamil": "ஆரோக்கியமான செடி",
        "cause": "நோய் இல்லை",
        "treatment": "சிகிச்சை தேவையில்லை",
        "prevention": "சரியான பராமரிப்பு செய்யவும்"
    }
}

def predict_disease(path):
    img = cv2.imread(path)
    if img is None:
        return "Healthy"
    img = cv2.resize(img,(224,224))
    green = np.mean(img[:,:,1])
    return "Healthy" if green > 130 else "Leaf Spot"

# ✅ SAFE VOICE (NO CRASH)
def make_voice(text):
    try:
        filename = f"{uuid.uuid4()}.mp3"
        path = os.path.join(AUDIO_FOLDER, filename)
        gTTS(text=text, lang="ta").save(path)
        return f"/static/audio/{filename}"
    except:
        return ""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        file = request.files["file"]
        filename = str(uuid.uuid4()) + ".jpg"
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        d = predict_disease(path)
        info = disease_data[d]

        text = f"""
🌿 {info['tamil']}

காரணம்:
{info['cause']}

தீர்வு:
{info['treatment']}

தடுப்பு:
{info['prevention']}
"""

        return jsonify({
            "text": text,
            "audio": make_voice(text)
        })
    except:
        return jsonify({"text": "Error in prediction", "audio": ""})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        q = request.json["msg"].lower()

        if "water" in q or "தண்ணி" in q:
            r = "ஒரு நாளைக்கு 0.5 முதல் 1 லிட்டர் தண்ணீர் போதுமானது."
        elif "sun" in q or "வெயில்" in q:
            r = "ஒரு நாளைக்கு 6 முதல் 8 மணி நேரம் வெயில் அவசியம்."
        elif "fertilizer" in q or "உரம்" in q:
            r = "10 முதல் 15 நாட்களுக்கு ஒருமுறை உரம் பயன்படுத்தவும்."
        else:
            r = "தண்ணீர், வெயில், உரம் பற்றி கேளுங்கள்."

        return jsonify({
            "reply": r,
            "audio": make_voice(r)
        })
    except:
        return jsonify({"reply": "Error", "audio": ""})

@app.route("/weather")
def weather():
    try:
        data = requests.get(
            "https://api.open-meteo.com/v1/forecast?latitude=13.08&longitude=80.27&current_weather=true",
            timeout=3
        ).json()

        temp = data["current_weather"]["temperature"]
        text = f"இப்போது வெப்பநிலை {temp}°C"

        return jsonify({
            "text": text,
            "audio": make_voice(text)
        })
    except:
        return jsonify({
            "text": "வானிலை கிடைக்கவில்லை",
            "audio": ""
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
