# WhatsApp Campaign Manager

A full-stack web application for managing contacts, message templates, and WhatsApp outreach campaigns with real-time delivery tracking.

Built with **FastAPI**, **SQLAlchemy**, and **Vanilla JavaScript** — featuring JWT authentication, group-based targeting, CSV import, scheduled campaigns, analytics dashboard, and WebSocket progress updates.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat&logo=javascript&logoColor=black)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red?style=flat)

---

## Features

- **User Authentication** — Register, login, profile updates, and password change with JWT tokens
- **Contact Management** — CRUD operations, tagging, and bulk CSV import
- **Group Management** — Organize contacts into groups for targeted campaigns
- **Message Templates** — Reusable templates with `{{name}}`, `{{phone_number}}`, and `{{tags}}` placeholders
- **Campaign Composer** — Send to groups or individual contacts, with optional scheduling
- **Analytics Dashboard** — Track total sent, success/failure counts, success rate, and recent activity
- **Real-time Updates** — WebSocket-powered live progress during message dispatch
- **Security** — Environment-based config, rate limiting on auth and send endpoints, authenticated WebSockets

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | FastAPI, SQLAlchemy, APScheduler, SlowAPI, python-jose, passlib |
| Frontend | HTML5, CSS3 (Glassmorphism UI), Vanilla JavaScript |
| Database | SQLite |
| Messaging | pywhatkit (browser automation proof-of-concept) |
| Real-time | WebSockets |

---

## Project Structure

```
whatsapp-campaign-manager/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # SQLAlchemy ORM models
│   ├── database.py          # Database connection
│   ├── auth_utils.py        # JWT & password utilities
│   ├── routers/             # API route modules
│   ├── scheduler.py         # APScheduler for delayed campaigns
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── tests/
│   └── test_api.py
├── sample_contacts.csv
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Google Chrome (required by pywhatkit for WhatsApp Web automation)
- WhatsApp Web logged in on the machine running the server

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/whatsapp-campaign-manager.git
   cd whatsapp-campaign-manager
   ```

2. **Create a virtual environment**
   ```bash
   cd backend
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   copy .env.example .env   # Windows
   cp .env.example .env     # macOS/Linux
   ```
   Edit `.env` and set a strong random `SECRET_KEY`.

5. **Run the server**
   ```bash
   uvicorn main:app --reload
   ```

6. **Open the app**
   Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create a new account |
| POST | `/auth/login` | Login and receive JWT token |
| GET | `/auth/me` | Get current user profile |
| GET/POST | `/contacts/` | List or create contacts |
| POST | `/contacts/import` | Bulk import from CSV |
| GET/POST | `/contacts/groups` | List or create groups |
| GET/POST | `/templates/` | List or create templates |
| POST | `/messages/send` | Send or schedule a campaign |
| GET | `/analytics/stats` | Campaign statistics |
| GET | `/analytics/logs` | Message delivery logs |
| WS | `/ws/progress?token=` | Real-time send progress |

Interactive API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## CSV Import Format

Use `sample_contacts.csv` as a reference:

```csv
name,phone_number,tags
John Doe,+1234567890,"friends,test"
Jane Smith,+1987654321,family
```

---

## Important Notes

### Messaging Engine (pywhatkit)

This project uses **pywhatkit** as a proof-of-concept messaging engine. It automates WhatsApp Web via browser control on the **local machine** where the server runs. It is **not** a production WhatsApp Business API integration.

For demos and portfolio purposes, this demonstrates the campaign workflow (templating, scheduling, logging, analytics). In production, you would replace pywhatkit with the [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp) or a provider like Twilio.

### Security

- Never commit your `.env` file — use `.env.example` as a template
- Rate limits: 5 requests/min on login & register, 2 requests/min on message send
- WebSocket connections require a valid JWT token

---

## Running Tests

```bash
cd backend
pytest ../tests -v
```

---

## Resume / Portfolio Highlights

- Designed and built a full-stack campaign management platform from scratch
- Implemented secure REST API with JWT auth, rate limiting, and role-scoped data access
- Integrated real-time WebSocket updates for live campaign monitoring
- Built a responsive glassmorphism UI with search, filtering, and CRUD operations
- Added scheduled job processing with APScheduler and background task handling

---

## License

MIT License — free to use for portfolio and learning purposes.
