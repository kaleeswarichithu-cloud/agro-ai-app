from flask import Flask, render_template, request, jsonify
import os, uuid, numpy as np
from PIL import Image
from gtts import gTTS
import requests
import random

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
AUDIO_FOLDER = "static/audio"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# ✅ 30+ diseases dataset
disease_data = {}

for i in range(1, 51):
    disease_data[f"Disease_{i}"] = {
        "tamil": f"நோய் {i}",
        "cause": "பல்வேறு காரணங்கள்",
        "treatment": "பொருத்தமான நாசினி பயன்படுத்தவும்",
        "prevention": "சரியான பராமரிப்பு"
    }

# add some real names also
disease_data.update({
    "Healthy": {"tamil":"ஆரோக்கியம்","cause":"நோய் இல்லை","treatment":"தேவை இல்லை","prevention":"சரியான பராமரிப்பு"},
    "Leaf Spot": {"tamil":"இலை புள்ளி","cause":"பூஞ்சை","treatment":"நீம் எண்ணெய்","prevention":"ஈரத்தை குறைக்கவும்"},
    "Powdery Mildew": {"tamil":"பொடிமை","cause":"பூஞ்சை","treatment":"நாசினி","prevention":"காற்றோட்டம்"},
})

# ❗ TEMP FAKE AI (replace later with real model)
def predict_disease(path):
    try:
        img = Image.open(path).resize((224,224))
        arr = np.array(img)

        # simple feature
        avg = np.mean(arr)

        # simulate multi-class
        keys = list(disease_data.keys())
        index = int(avg) % len(keys)

        return keys[index]

    except:
        return "Healthy"

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
        if "file" not in request.files:
            return jsonify({"text":"No file","audio":""})

        file = request.files["file"]
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        d = predict_disease(path)
        info = disease_data.get(d, disease_data["Healthy"])

        text = f"""
🌿 {info['tamil']}
காரணம்: {info['cause']}
தீர்வு: {info['treatment']}
தடுப்பு: {info['prevention']}
"""

        return jsonify({
            "text": text,
            "audio": make_voice(text)
        })

    except Exception as e:
        return jsonify({"text":str(e),"audio":""})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        q = request.json.get("msg","").lower()

        if "water" in q:
            r = "0.5 முதல் 1 லிட்டர் தண்ணீர் போதுமானது"
        elif "sun" in q:
            r = "6–8 மணி நேரம் வெயில்"
        else:
            r = "வேறு கேள்வி கேளுங்கள்"

        return jsonify({
            "reply": r,
            "audio": make_voice(r)
        })

    except Exception as e:
        return jsonify({"reply":str(e),"audio":""})

@app.route("/weather")
def weather():
    try:
        data = requests.get(
            "https://api.open-meteo.com/v1/forecast?latitude=13.08&longitude=80.27&current_weather=true"
        ).json()

        temp = data["current_weather"]["temperature"]
        text = f"வெப்பநிலை {temp}°C"

        return jsonify({
            "text": text,
            "audio": make_voice(text)
        })

    except:
        return jsonify({"text":"Weather error","audio":""})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
