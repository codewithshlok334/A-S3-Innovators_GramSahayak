import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ================= CONFIG =================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set. Please add it to your .env file.")

if not WEATHER_API_KEY:
    raise RuntimeError("WEATHER_API_KEY not set. Please add it to your .env file.")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ================= ROUTES =================

@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "Backend running"})

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()

    if not data or "prompt" not in data:
        return jsonify({"error": "Missing prompt"}), 400

    prompt = data["prompt"]
    system_instruction = data.get(
        "systemInstruction",
        "You are GramSahayak AI. Respond in simple Hindi using Devanagari."
    )

    # Updated to a confirmed working model name (as of early 2025)
    payload = {
        "model": "llama-3.3-70b-versatile",  # ✅ FIXED: use a current model
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        
        # Log the error if status is not 200 (for debugging)
        if r.status_code != 200:
            print(f"Groq API Error {r.status_code}: {r.text}")
            return jsonify({"error": f"Groq API returned {r.status_code}: {r.text}"}), r.status_code

        reply = r.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to Groq API timed out."}), 504
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return jsonify({"error": f"Network error: {str(e)}"}), 502
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/api/weather")
def weather():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if not lat or not lon:
        return jsonify({"error": "Missing lat/lon"}), 400

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&units=metric&appid={WEATHER_API_KEY}"
    )

    try:
        r = requests.get(url, timeout=10)
        
        # OpenWeatherMap returns 401 for invalid keys
        if r.status_code == 401:
            print("OpenWeatherMap API returned 401: Invalid API key")
            return jsonify({"error": "Invalid Weather API key. Please check your .env file."}), 401
        elif r.status_code != 200:
            print(f"OpenWeatherMap API Error {r.status_code}: {r.text}")
            return jsonify({"error": f"Weather API error: {r.text}"}), r.status_code

        return jsonify(r.json())
    except requests.exceptions.Timeout:
        return jsonify({"error": "Weather API request timed out."}), 504
    except requests.exceptions.RequestException as e:
        print(f"Weather API network error: {e}")
        return jsonify({"error": f"Network error: {str(e)}"}), 502
    except Exception as e:
        print(f"Unexpected weather error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)