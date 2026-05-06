import os
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request


load_dotenv()

app = Flask(__name__)

SYSTEM_PROMPT = (
    "You are an AI WhatsApp assistant for a business. Reply in a helpful, "
    "polite, and concise way. Keep responses short and WhatsApp-friendly."
)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"
GRAPH_API_VERSION = "v20.0"
REQUEST_TIMEOUT_SECONDS = 15


def get_env(name: str) -> str | None:
    value = os.getenv(name)
    if not value:
        print(f"Missing required environment variable: {name}")
        return None
    return value


def log_api_error(service: str, response: requests.Response) -> None:
    try:
        error_body: Any = response.json()
    except ValueError:
        error_body = response.text[:500]

    print(
        f"{service} API error: status={response.status_code}, "
        f"response={error_body}"
    )


def extract_text_message(payload: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    try:
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])

                if not messages:
                    continue

                message = messages[0]
                sender = message.get("from")
                message_type = message.get("type")

                if message_type != "text":
                    return sender, None, message_type or "unknown"

                text = message.get("text", {})
                body = text.get("body", "").strip()
                return sender, body, "text"
    except AttributeError:
        print("Malformed webhook payload structure")

    return None, None, None


def get_groq_reply(user_message: str) -> str | None:
    api_key = get_env("GROQ_API_KEY")
    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 250,
    }

    try:
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        print(f"Groq request failed: {exc}")
        return None

    if response.status_code >= 400:
        log_api_error("Groq", response)
        return None

    try:
        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        print(f"Could not parse Groq response: {exc}")
        return None

    return reply or None


def send_whatsapp_text(to_phone_number: str, message: str) -> bool:
    whatsapp_token = get_env("WHATSAPP_TOKEN")
    phone_number_id = get_env("PHONE_NUMBER_ID")
    if not whatsapp_token or not phone_number_id:
        return False

    url = (
        f"https://graph.facebook.com/{GRAPH_API_VERSION}/"
        f"{phone_number_id}/messages"
    )
    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone_number,
        "type": "text",
        "text": {"body": message},
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        print(f"WhatsApp request failed: {exc}")
        return False

    if response.status_code >= 400:
        log_api_error("WhatsApp", response)
        return False

    return True


@app.get("/")
def index():
    return "WhatsApp AI Bot is running"


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    verify_token = get_env("VERIFY_TOKEN")

    if mode == "subscribe" and token and token == verify_token:
        print("Webhook verified successfully")
        return challenge or "", 200

    print("Webhook verification failed")
    return "Forbidden", 403


@app.post("/webhook")
def handle_webhook():
    try:
        payload = request.get_json(silent=True) or {}
        sender, message_body, message_type = extract_text_message(payload)

        if not sender and not message_body and not message_type:
            print("Ignoring webhook without a user message")
            return jsonify({"status": "ignored"}), 200

        if message_type != "text":
            print(f"Ignoring unsupported message type: {message_type}")
            return jsonify({"status": "ignored"}), 200

        if not sender:
            print("Ignoring text message without sender")
            return jsonify({"status": "ignored"}), 200

        if not message_body:
            print(f"Ignoring empty text message from sender ending in {sender[-4:]}")
            return jsonify({"status": "ignored"}), 200

        print(f"Received text message from sender ending in {sender[-4:]}")
        ai_reply = get_groq_reply(message_body)
        if not ai_reply:
            ai_reply = "Sorry, I could not process that right now. Please try again soon."

        send_whatsapp_text(sender, ai_reply)
        return jsonify({"status": "processed"}), 200
    except Exception as exc:
        print(f"Unexpected webhook handling error: {exc}")
        return jsonify({"status": "error"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
