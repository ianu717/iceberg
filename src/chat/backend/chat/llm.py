""" GROQ
"""
from groq import Groq
from .config import GROQ_API_KEY, GROQ_MODEL

_client = None

def init_llm() -> None:
    global _client
    if not GROQ_API_KEY:
        raise EnvironmentError("GROQ_API_KEY no encontrada en .env")
    _client = Groq(api_key=GROQ_API_KEY)

def call_llm(prompt: str, system_prompt: str) -> str:
    
    print(f"DEBUG messages[0] role: system")
    print(f"DEBUG messages[0] content: {system_prompt[:80]}")
    print(f"DEBUG messages[1] role: user")
    print(f"DEBUG messages[1] content: {prompt[:80]}")

    response = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content

# """
# Integración con Gemini API mediante google-generativeai.
# """

# import google.genai as genai
# from .config import GEMINI_API_KEY, GEMINI_MODEL

# _client = None

# def init_gemini() -> None:
#     global _client
#     if not GEMINI_API_KEY:
#         raise EnvironmentError(
#             "GEMINI_API_KEY no encontrada. "
#             "Define la variable de entorno antes de iniciar el servidor."
#         )
#     _client = genai.Client(api_key=GEMINI_API_KEY)

# def call_llm(prompt: str, system_prompt: str) -> str:
#     print(f"DEBUG system_prompt: {system_prompt[:100]}")
#     print(f"DEBUG prompt: {prompt[:200]}")
#     model = _client.models
#     response = model.generate_content(
#         model=GEMINI_MODEL,
#         contents=prompt,
#         config={
#             "system_instruction": system_prompt,
#         }
#     )
#     return response.text