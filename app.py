from flask import Flask, request, jsonify, render_template
from google import genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
CHAT_FOLDER = "chats"
os.makedirs(CHAT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


# ---------------- GET CHATS ----------------
@app.route("/get_chats", methods=["GET"])
def get_chats():
    chats = []

    for file in os.listdir(CHAT_FOLDER):
        if file.endswith(".json"):
            chat_id = file.replace(".json", "")
            title_file = f"{CHAT_FOLDER}/{chat_id}_title.txt"

            if os.path.exists(title_file):
                with open(title_file, "r") as f:
                    title = f.read()
            else:
                title = "New Chat"

            chats.append({"id": chat_id, "name": title})

    return jsonify({"chats": chats})


# ---------------- NEW CHAT ----------------
@app.route("/new_chat", methods=["POST"])
def new_chat():
    chat_id = str(len(os.listdir(CHAT_FOLDER)) + 1)

    with open(f"{CHAT_FOLDER}/{chat_id}.json", "w") as f:
        json.dump([], f)

    return jsonify({"chat_id": chat_id})


# ---------------- DELETE CHAT ----------------
@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    chat_id = request.json.get("chat_id")

    json_file = f"{CHAT_FOLDER}/{chat_id}.json"
    title_file = f"{CHAT_FOLDER}/{chat_id}_title.txt"

    if os.path.exists(json_file):
        os.remove(json_file)

    if os.path.exists(title_file):
        os.remove(title_file)

    return jsonify({"status": "Deleted"})


# ---------------- LOAD CHAT HISTORY ----------------
@app.route("/get_chat_history", methods=["GET"])
def get_chat_history():
    chat_id = request.args.get("chat_id")
    file_path = f"{CHAT_FOLDER}/{chat_id}.json"

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            history = json.load(f)
        return jsonify({"messages": history})

    return jsonify({"messages": []})


# ---------------- SEND MESSAGE (STREAMING) ----------------
@app.route("/send_message", methods=["POST"])
def send_message():
    chat_id = request.json.get("chat_id")
    message = request.json.get("message")

    file_path = f"{CHAT_FOLDER}/{chat_id}.json"

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            history = json.load(f)
    else:
        history = []

    history.append({"role": "user", "content": message})

    # First message becomes title
    if len(history) == 1:
        title = message[:40]
        with open(f"{CHAT_FOLDER}/{chat_id}_title.txt", "w") as f:
            f.write(title)

    # Convert history to text format for Gemini
    formatted_history = ""
    for msg in history:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted_history += f"{role}: {msg['content']}\n"

    def generate():
        response = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=formatted_history
        )

        full_reply = ""

        for chunk in response:
            if chunk.text:
                full_reply += chunk.text
                yield chunk.text

        history.append({"role": "assistant", "content": full_reply})

        with open(file_path, "w") as f:
            json.dump(history, f, indent=2)

    return app.response_class(generate(), mimetype='text/plain')


if __name__ == "__main__":
    app.run(debug=True)
