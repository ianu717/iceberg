# test_gemini.py
import os
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="models/gemini-2.0-flash",
    contents="di hola en inglés",
)
print(response.text)