from flask import Flask, render_template, request, jsonify
import os, sqlite3, requests
import numpy as np
import cv2
from gtts import gTTS
from tensorflow.keras.models import load_model

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# LOAD MODEL
model = load_model("model/model.h5")

classes = ["Healthy", "Leaf Spot", "Leaf Blight"]

# DATABASE
conn = sqlite3.connect("farm.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS results(
id INTEGER PRIMARY KEY,
disease TEXT,
score REAL
)
""")
conn.commit()

# WEATHER
def get_weather():
    try:
        url = "http://api.openweathermap.org/data/2.5/weather?q=Chennai&appid=YOUR_KEY&units=metric"
        r = requests.get(url).json()
        return f"{r['main']['temp']}°C, {r['weather'][0]['description']}"
    except:
        return "Weather unavailable"

@app.route("/")
def home():
    return render_template("index.html")

# AI PREDICTION
@app.route("/predict", methods=["POST"])
def predict():
    file = request.files["image"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    img = cv2.imread(path)
    img = cv2.resize(img, (224,224))
    img = img / 255.0
    img = np.reshape(img, (1,224,224,3))

    pred = model.predict(img)
    idx = np.argmax(pred)

    disease = classes[idx]
    score = round(float(np.max(pred)) * 100, 2)

    # FARMER FRIENDLY LOGIC
    if disease == "Healthy":
        treatment = ["No disease", "Continue normal watering"]
        routine = ["Water daily 500ml", "Give sunlight"]
        prevention = ["Keep soil healthy"]

    elif disease == "Leaf Spot":
        treatment = ["Remove spotted leaves", "Spray neem oil"]
        routine = ["Check leaves daily", "Avoid wet leaves"]
        prevention = ["Maintain spacing"]

    else:
        treatment = ["Apply fungicide", "Reduce watering"]
        routine = ["Morning check", "Evening watering"]
        prevention = ["Avoid excess moisture"]

    weather = get_weather()

    # SAVE TO DB
    cursor.execute("INSERT INTO results(disease,score) VALUES (?,?)",(disease,score))
    conn.commit()

    # VOICE (Tamil)
    tts = gTTS(text=f"உங்கள் செடி {disease}", lang='ta')
    tts.save("static/output.mp3")

    return jsonify({
        "disease": disease,
        "score": score,
        "treatment": treatment,
        "routine": routine,
        "prevention": prevention,
        "weather": weather,
        "audio": "/static/output.mp3"
    })

# CHAT
@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json["msg"].lower()

    if "water" in msg:
        reply = "500ml to 1 liter daily depending on plant"
    elif "rice" in msg:
        reply = "Maintain 2-5 cm water level"
    else:
        reply = "Ask about crop like tomato or rice"

    tts = gTTS(text=reply, lang='ta')
    tts.save("static/output.mp3")

    return jsonify({"reply": reply, "audio": "/static/output.mp3"})

if __name__ == "__main__":
    print("🚀 Agro AI running")
    app.run(debug=True)