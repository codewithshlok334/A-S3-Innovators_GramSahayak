import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==================== CONFIGURATION ====================
# इन्हें environment variables से सेट करें या सीधे यहाँ बदलें
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyB886btt8t9NOA7JW3agja3F6vhi7EfCEo")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "9d35fd198b820775f857b6830f79bed8")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    """रूट एंडपॉइंट – बताता है कि बैकएंड चालू है"""
    return jsonify({
        "status": "ok",
        "message": "GramSahayak Backend is running",
        "endpoints": {
            "/api/chat": "POST – Gemini AI chat",
            "/api/weather": "GET – Real-time weather (requires lat, lon)"
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Gemini AI से बातचीत के लिए प्रॉक्सी एंडपॉइंट
    Request body: { "prompt": "...", "systemInstruction": "..." }
    Response: { "reply": "..." } या error
    """
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Missing prompt'}), 400

    prompt = data['prompt']
    system_instruction = data.get('systemInstruction', '')

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status()
        gemini_data = response.json()
        reply = gemini_data.get('candidates', [{}])[0] \
                          .get('content', {}) \
                          .get('parts', [{}])[0] \
                          .get('text', 'कोई उत्तर नहीं')
        return jsonify({'reply': reply})
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    except (KeyError, IndexError) as e:
        return jsonify({'error': 'Invalid response from Gemini'}), 502

@app.route('/api/weather', methods=['GET'])
def weather():
    """
    OpenWeatherMap से मौसम लाने के लिए प्रॉक्सी एंडपॉइंट
    Query params: lat, lon
    Returns: OpenWeatherMap API का JSON response
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({'error': 'Missing lat/lon parameters'}), 400

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={WEATHER_API_KEY}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

# ==================== MAIN ====================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)