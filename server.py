import os, json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import anthropic

app = Flask(__name__)
CORS(app)

# Chiavi di accesso autorizzate
VALID_KEYS = {
    "RMI-EGLIN-PAOLO",
    "RMI-EGLIN-KEY2",
    "RMI-EGLIN-KEY3",
}

def check_key(req):
    key = req.headers.get("X-API-Key", "")
    return key in VALID_KEYS

@app.route("/api", methods=["POST"])
def api():
    if not check_key(request):
        return jsonify({"error": "Non autorizzato"}), 401
    data = request.json
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=data.get("messages", [])
    )
    return jsonify({"content": message.content[0].text})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
