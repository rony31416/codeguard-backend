"""
SIMPLE FUCKING EXAMPLE - Gemini 2.0 Flash
==========================================

This is how you use it. Period.
"""

import os
from dotenv import load_dotenv
from google import genai

# 1. Load your API key from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 2. Create client
client = genai.Client(api_key=api_key)

# 3. Generate content
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Explain AI in 5 words"
)

# 4. Get response
print(response.text)


# That's it. 3 lines of actual code.
# Example usage in your code:

def ask_gemini(question: str) -> str:
    """Ask Gemini anything."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=question
    )
    return response.text


# Use it:
# answer = ask_gemini("What is a bug?")
# print(answer)
