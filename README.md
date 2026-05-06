# WhatsApp AI Chatbot with Flask and Groq

A production-ready Flask backend for Meta WhatsApp Cloud API webhooks. It receives WhatsApp text messages, sends them to Groq, and replies through the WhatsApp Cloud API.

This project is ready for the GitHub repo:

```text
https://github.com/althaf-zyan/chatbot
```

## What You Need

- Python 3.11 or newer
- A Meta Developer account
- A WhatsApp Cloud API app and phone number
- A Groq API key
- A GitHub account
- A Render account
- Optional: cron-job.org account to keep the free Render service warm

## Project Files

- `main.py` - Flask app, webhook routes, Groq integration, and WhatsApp sending
- `requirements.txt` - Python dependencies
- `render.yaml` - Render Blueprint deployment config
- `.env.example` - Example environment variables
- `.gitignore` - Keeps local secrets and generated files out of Git

## Environment Variables

Copy `.env.example` to `.env` for local development:

```bash
cp .env.example .env
```

Fill in the values:

```env
VERIFY_TOKEN=my_cool_bot_2026
WHATSAPP_TOKEN=your_meta_whatsapp_token_here
PHONE_NUMBER_ID=your_whatsapp_phone_number_id_here
GROQ_API_KEY=your_groq_api_key_here
```

`VERIFY_TOKEN` is a secret string you choose. You will enter the same value in the Meta webhook setup screen. Meta sends it to your `/webhook` endpoint to prove that you own the server.

Never commit your real `.env` file.

Important: if an API token was pasted into a chat, issue tracker, README, or public place, rotate it before production use. Put real tokens only in your local `.env` file and in Render environment variables.

## Run Locally

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your real credentials.

Start the Flask app:

```bash
python main.py
```

The app will run at:

```text
http://localhost:5000
```

Check the health routes:

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```

Expected responses:

```text
WhatsApp AI Bot is running
```

```json
{"status":"ok"}
```

To test Meta webhooks locally, expose your local server with ngrok:

```bash
ngrok http 5000
```

Use the ngrok HTTPS URL plus `/webhook` as the temporary Meta callback URL.

## Push to GitHub

Initialize Git:

```bash
git init
git add .
git commit -m "Initial WhatsApp AI chatbot"
```

Create or open this GitHub repository:

```text
https://github.com/althaf-zyan/chatbot
```

Then connect and push:

```bash
git branch -M main
git remote add origin https://github.com/althaf-zyan/chatbot.git
git push -u origin main
```

Confirm `.env` was not committed:

```bash
git status
```

## Deploy on Render

You can deploy using the included `render.yaml` Blueprint or by creating a Web Service manually.

### Option 1: Render Blueprint

1. Push this project to GitHub.
2. Open Render.
3. Choose **New +**.
4. Choose **Blueprint**.
5. Connect your GitHub repository.
6. Render will detect `render.yaml`.
7. Add the required environment variables:
   - `VERIFY_TOKEN`
   - `WHATSAPP_TOKEN`
   - `PHONE_NUMBER_ID`
   - `GROQ_API_KEY`
8. Deploy.

### Option 2: Render Web Service

1. Open Render.
2. Choose **New +**.
3. Choose **Web Service**.
4. Connect your GitHub repository.
5. Use these settings:
   - Runtime: Python
   - Branch: `main`
   - Root Directory: leave empty
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn main:app`
6. Add the required environment variables.
7. Deploy.

After deployment, your app URL will look like:

```text
https://your-render-app.onrender.com
```

Your Meta callback URL will be:

```text
https://your-render-app.onrender.com/webhook
```

For your Render service named `chatbot`, the final URL may look similar to:

```text
https://chatbot-xxxx.onrender.com/webhook
```

## Meta WhatsApp Webhook Setup

1. Go to Meta for Developers.
2. Open your app.
3. Go to WhatsApp > Configuration.
4. Find the Webhooks section.
5. Set Callback URL to:

```text
https://your-render-app.onrender.com/webhook
```

6. Set Verify token to the same value as your `VERIFY_TOKEN` environment variable.
7. Click Verify and Save.
8. Subscribe to the webhook field:

```text
messages
```

Now send a WhatsApp message to your Cloud API test or production number. The bot should reply with a short AI response.

## cron-job.org Warm Ping

Render free services may sleep when inactive. To keep the app warm:

1. Create a cron-job.org account.
2. Create a new cron job.
3. Set the URL to:

```text
https://your-render-app.onrender.com/health
```

4. Set the schedule to every 14 minutes.
5. Save and enable the job.

## Common Troubleshooting

### Meta webhook verification fails

- Confirm your Render app is deployed successfully.
- Confirm the callback URL ends with `/webhook`.
- Confirm the verify token in Meta exactly matches `VERIFY_TOKEN` in Render.
- Check Render logs for `Webhook verification failed`.

### Bot receives messages but does not reply

- Confirm `WHATSAPP_TOKEN` is valid and not expired.
- Confirm `PHONE_NUMBER_ID` is the WhatsApp phone number ID, not the display phone number.
- Confirm you subscribed to the `messages` webhook field.
- Check Render logs for WhatsApp API errors.
- Confirm the recipient is allowed to receive messages from your Meta test number.

### Groq replies fail

- Confirm `GROQ_API_KEY` is set in Render.
- Confirm your Groq account has API access.
- Check Render logs for Groq API errors.
- If the key was exposed anywhere, rotate it and update Render.

### Render deploy fails

- Confirm `requirements.txt` exists.
- Confirm the start command is `gunicorn main:app`.
- Confirm Python version is 3.11 or newer.

### App works locally but not on Render

- Confirm all environment variables are set in Render.
- Redeploy after changing environment variables.
- Check the service logs in Render.

### Webhook works but Meta retries

- The app returns HTTP 200 immediately for POST `/webhook`.
- If retries continue, check Render logs for cold starts or service crashes.
- Add the cron-job.org warm ping to reduce cold starts on free Render services.

## Security Notes

- Do not hardcode API keys.
- Do not commit `.env`.
- Keep WhatsApp and Groq tokens private.
- Rotate tokens if they are accidentally exposed.
- The webhook POST route always returns HTTP 200 so Meta does not retry unnecessarily.
- The app logs only high-level status and the last four digits of a sender number.
