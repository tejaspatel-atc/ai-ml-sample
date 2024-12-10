import json

import requests
from app.settings import settings


async def escalateIssue(name, email, phone, bot_id, call_conversation):
    try:
        payload = {
            "session_id": None,
            "name": name,
            "email": email,
            "phone": phone,
            "bot_id": bot_id,
            "is_voice": True,
            "chat_history": call_conversation,
        }

        headers = {"Content-Type": "application/json"}

        response = requests.post(settings.SUMMARIZATION_URL, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"HTTP error! status: {response.status_code}")

        result = response.json()
        return json.dumps(result)

    except Exception as e:
        print(f"Error escalating issue: {e}")
        return "Unexpected Error Occurred. Please try again later."
