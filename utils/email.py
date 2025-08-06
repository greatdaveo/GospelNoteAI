import httpx
import os
from dotenv import load_dotenv

load_dotenv()


RESEND_API_KEY = os.getenv("RESEND_API_KEY")
# print("RESEND_API_KEY", RESEND_API_KEY)

FROM_EMAIL = os.getenv("FROM_EMAIL")

def send_email(to: str, subject: str, html: str):
    if not RESEND_API_KEY:
        raise ValueError("RESEND_API_KEY not set in environment")

    payload = {
        "from": FROM_EMAIL,
        "to": to,
        "subject": subject,
        "html": html
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = httpx.post("https://api.resend.com/emails", json = payload, headers = headers)
        response.raise_for_status()
    except httpx.HTTPError as e:
        print(f"Failed to send email: {e}")
        raise
