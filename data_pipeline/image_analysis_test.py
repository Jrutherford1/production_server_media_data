import requests
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY is not set. Make sure it is defined in your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)

image_url = "https://www.library.illinois.edu/ias/wp-content/uploads/sites/20/2025/01/cropped-UI-04-171214-129d.jpg"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

data = {
    "model": "gpt-4o",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Generate a concise and accurate alt text description for accessibility, one sentence no more than 10 words."},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ],
    "max_tokens": 100
}

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)

if response.status_code == 200:
    alt_text = response.json()['choices'][0]['message']['content']
    print("Generated alt text:", alt_text)
else:
    print("Error:", response.status_code, response.text)