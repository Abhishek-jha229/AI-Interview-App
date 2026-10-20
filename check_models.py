import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Available models for your key:\n")
for m in client.models.list().data:
    print(m.id)