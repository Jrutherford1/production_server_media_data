import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Retrieve the API key from the environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY is not set. Make sure it is defined in your .env file.")

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Example request
response = client.responses.create(
    model="gpt-4.1",
    input="Write a 50-word story about a Harley Davidson motorcycle."
)

# Print the response
print(response.output_text)