# ShopMate – E-Commerce Customer Support Chatbot

ShopMate is an AI-powered e-commerce customer support chatbot built with FastAPI, Groq, WebSockets, and Retrieval-Augmented Generation (RAG). It can answer customer FAQs and retrieve order information while streaming responses in real time through a web interface.

## Features

- AI-powered customer support using Groq.
- Real-time response streaming using WebSockets.
- Order status lookup using function calling.
- FAQ retrieval using ChromaDB and RAG.
- Simple HTML, CSS, and JavaScript frontend.

## Technologies Used

- Python
- FastAPI
- WebSockets
- Groq API
- ChromaDB
- HTML, CSS, JavaScript

## Project Setup

### 1. Clone the repository

```bash
git clone https://github.com/shumyzesKhnx/shumyze-ecommerce-bot.git
cd shumyze-ecommerce-bot
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root and add:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_model_name
```

Replace the placeholders with your actual Groq API key and the model name you want to use.

### 5. Ingest the FAQs

Run the following command to load the FAQ data into ChromaDB:

```bash
python ingest.py
```

This creates or updates the persistent vector database used for FAQ retrieval.

### 6. Start the FastAPI server

Run:

```bash
uvicorn main:app --reload
```

### 7. Open the chatbot

Open your browser and navigate to:

http://localhost:8000

You can now interact with ShopMate through the web interface.

## Project Structure

```text
.
├── main.py
├── ingest.py
├── faqs.json
├── index.html
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Notes

- The order database contains mock order data for demonstration.
- The chatbot requires a valid Groq API key.
- FAQ data is stored and retrieved using ChromaDB.
