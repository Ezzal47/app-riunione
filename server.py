import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
from openai import OpenAI
import tempfile

app = Flask(__name__)
CORS(app)

VALID_KEYS = {
    "RMI-EGLIN-PAOLO",
    "RMI-EGLIN-KEY2",
    "RMI-EGLIN-KEY3",
}

def check_key(req):
    # Accetta chiave sia nell'header che nel form data
    key = req.headers.get("X-API-Key", "") or req.form.get("api_key", "") or req.args.get("api_key", "")
    return key in VALID_KEYS

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

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

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if not check_key(request):
        return jsonify({"error": "Non autorizzato"}), 401
    if "file" not in request.files:
        return jsonify({"error": "Nessun file ricevuto"}), 400
    f = request.files["file"]
    suffix = os.path.splitext(f.filename)[1] or ".mp3"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="it"
            )
        return jsonify({"text": result.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
