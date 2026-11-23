# ShopMate – E-Commerce Chatbot

An AI-powered customer support chatbot built with FastAPI, Groq, WebSockets, and ChromaDB (RAG). It answers FAQs, retrieves mock order information, and streams responses through a web interface.

## Features
- Streaming responses via WebSockets
- Order status lookup using function calling
- FAQ retrieval using ChromaDB
- HTML, CSS, and JavaScript frontend

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/shumyzesKhnx/shumyze-ecommerce-bot.git
cd shumyze-ecommerce-bot
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
```
Windows:
```powershell
.\venv\Scripts\Activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure `.env`
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_api_key
GROQ_MODEL=your_model_name
```

### 5. Ingest FAQs
```bash
python ingest.py
```

### 6. Run the server
```bash
uvicorn main:app --reload
```

### 7. Open the chatbot
Visit http://localhost:8000

## Files
- `main.py` – FastAPI app, WebSocket chat, Groq and tool calling
- `ingest.py` – FAQ ingestion and vector search
- `faqs.json` – FAQ data
- `index.html` – Chat interface
- `requirements.txt` – Dependencies
