# import os
# from groq import Groq
# from dotenv import load_dotenv

# load_dotenv()
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# try:
#     response = client.chat.completions.create(
#         model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
#         messages=[{"role": "user", "content": "Hello"}],
#     )
#     print("Success:", response.choices[0].message.content)
# except Exception as e:
#     print("Error:", e)
