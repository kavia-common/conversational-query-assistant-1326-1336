# Chatbot Backend (Django) - Quickstart

A lightweight Django REST API that proxies questions to OpenAI via LangChain.

## Prerequisites
- Python 3.11+ recommended
- pip

## Setup
1. Install dependencies:
   pip install -r requirements.txt

2. (Optional) Configure environment:
   cp .env.example .env
   # Edit .env to set:
   # - OPENAI_API_KEY if you want /api/chat/ to work
   # - ALLOWED_HOSTS if you want to restrict allowed host headers (comma-separated)
   #   e.g., ALLOWED_HOSTS=localhost,127.0.0.1,chatbot_frontend

3. Run development server:
   python manage.py runserver 0.0.0.0:8000

4. Test health:
   GET http://localhost:8000/api/health/  -> {"message": "Server is up!"}

5. Chat endpoint:
   POST http://localhost:8000/api/chat/
   Body: {"question": "Hello?"}
   Note: Requires OPENAI_API_KEY set in the environment. Without it, you will get a 500 error from the endpoint.

## Notes
- This project intentionally does not use a database; no migrations needed.
- Host headers:
  - To avoid "Invalid Host header" during development, the backend allows all hosts by default
    when ALLOWED_HOSTS env var is not set. For production, set ALLOWED_HOSTS explicitly
    (example: ALLOWED_HOSTS=api.example.com).
- API docs:
  - Swagger UI: http://localhost:8000/docs/
  - Redoc: http://localhost:8000/redoc/
  - OpenAPI JSON: http://localhost:8000/swagger.json
