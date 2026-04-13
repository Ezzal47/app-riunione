import os
import sys
import traceback
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
        print("AUTH FAILED", flush=True)
        return jsonify({"error": "Non autorizzato"}), 401

    if "file" not in request.files:
        print("NO FILE IN REQUEST", flush=True)
        return jsonify({"error": "Nessun file ricevuto"}), 400

    f = request.files["file"]
    print(f"FILE RECEIVED: {f.filename}, size approx", flush=True)

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai_key:
        print("ERROR: OPENAI_API_KEY not set", flush=True)
        return jsonify({"error": "OPENAI_API_KEY non configurata sul server"}), 500

    suffix = os.path.splitext(f.filename)[1] or ".mp3"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name
        size = os.path.getsize(tmp_path)
        print(f"SAVED TO {tmp_path}, size {size} bytes", flush=True)

    try:
        if size > 25 * 1024 * 1024:
            os.unlink(tmp_path)
            return jsonify({"error": "File troppo grande. Massimo 25 MB per Whisper."}), 400

        print("CALLING WHISPER...", flush=True)
        client = OpenAI(api_key=openai_key)
        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="it"
            )
        print(f"WHISPER OK: {len(result.text)} chars", flush=True)
        return jsonify({"text": result.text})

    except Exception as e:
        print(f"WHISPER ERROR: {e}", flush=True)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
