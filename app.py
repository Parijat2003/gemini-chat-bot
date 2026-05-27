from flask import Flask, request, jsonify, render_template
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# In-memory storage
chats = {}
chat_counter = 1


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get_chats", methods=["GET"])
def get_chats():
    chat_list = []

    for chat_id, chat_data in chats.items():
        chat_list.append({
            "id": str(chat_id),
            "name": chat_data["name"]
        })

    return jsonify({"chats": chat_list})


@app.route("/new_chat", methods=["POST"])
def new_chat():
    global chat_counter

    chats[chat_counter] = {
        "name": "New Chat",
        "messages": []
    }

    current_id = chat_counter
    chat_counter += 1

    return jsonify({"chat_id": str(current_id)})


@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    chat_id = int(request.json.get("chat_id"))

    if chat_id in chats:
        del chats[chat_id]

    return jsonify({"status": "Deleted"})


@app.route("/get_chat_history", methods=["GET"])
def get_chat_history():
    chat_id = int(request.args.get("chat_id"))

    if chat_id in chats:
        return jsonify({"messages": chats[chat_id]["messages"]})

    return jsonify({"messages": []})


@app.route("/send_message", methods=["POST"])
def send_message():
    chat_id = int(request.json.get("chat_id"))
    message = request.json.get("message")

    if chat_id not in chats:
         chats[chat_id] = {
        "name": "New Chat",
        "messages": []
    }
    chats[chat_id]["messages"].append({
        "role": "user",
        "content": message
    })

    # First message becomes chat title
    if chats[chat_id]["name"] == "New Chat":
        chats[chat_id]["name"] = message[:40]

    formatted_history = ""

    for msg in chats[chat_id]["messages"]:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted_history += f"{role}: {msg['content']}\n"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=formatted_history
    )

    bot_reply = response.text

    chats[chat_id]["messages"].append({
        "role": "assistant",
        "content": bot_reply
    })

    return jsonify({"reply": bot_reply})


if __name__ == "__main__":
    app.run()