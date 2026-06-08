import os
from dotenv import load_dotenv
#import google.generativeai as genai

load_dotenv()
#genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
load_dotenv()
key = os.getenv("GEMINI_API_KEY")
print(f"Key que se está usando: {key[:8]}...{key[-4:]}")
# for model in genai.list_models():
#     if "generateContent" in model.supported_generation_methods:
#         print(model.name)