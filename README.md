# AI-Chatbot-(Early Version)
> **Note:** This is an early prototype (v0.1.0) and may contain bugs.
## Overview
My AI is an internal company chatbot designed to assist employees by providing answers related to financial data, tax regulations, HR policies, etc. It features authenticated access with role-based permissions and department-specific knowledge, enhanced by AI-powered responses via integration with the Perplexity API.

## Features
- User authentication with JWT and OAuth2 password flow
- Role-based department access control
- Department-specific AI context and knowledge base
- Real-time chat powered by Perplexity AI API
- Conversation history management with save and delete functionality
- Secure password hashing via bcrypt
- Responsive web UI with support for light/dark mode

## Technology Stack
- **Backend:**
  - Python 3 with FastAPI
  - PostgreSQL using SQLAlchemy ORM
  - JWT Authentication with OAuth2
  - Password hashing with `passlib` (bcrypt)
  - Async HTTP client using `httpx` for AI calls
  - Environment management via `python-dotenv`
- **Frontend:**
  - Vanilla JavaScript with modular architecture
  - Fetch API for backend interaction
  - HTML5/CSS3 with responsive and accessible design
- **Third-Party API:**
  - Perplexity AI for advanced conversational responses

## Versioning

- **Current Version:** `v0.1.0`
- **Release Date:** 2025-08-04
- **Notes:** Initial release with core features; early prototype; may contain bugs.

## Installation

### Backend
1. Clone the repo.
2. Set up and activate a Python virtual environment.
3. Install dependencies from `requirements.txt`.
4. Configure `.env` with database URL, secrets, and API keys.
5. Run the backend using Uvicorn.

### Frontend
1. Serve `frontend` folder via a static server.
2. Access via browser at the server URL.

## Known Issues
- Being an early version, some features may be unstable.
- Minor bugs or UI glitches might be present.
- API integration depends on external service stability.
- User and department management functionality is basic.

## Contribution
Contributions are welcome to improve stability, add features, and fix bugs.

## License
MIT License 


