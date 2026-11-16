import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

response = client.chat.completions.create(
    model=os.getenv("GROQ_MODEL"),
    messages=[
        {
            "role": "system",
            "content": """
            You are an E-Commerce Customer
            Support Assistant.

            Help customers with orders,
            returns, shipping and warranties.

            Be polite and professional.
            """
        },
        {
            "role": "user",
            "content": "What is your return policy?"
        }
    ]
)

print(response.choices[0].message.content)