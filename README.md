# AI Travel Planner

A full-stack AI-powered travel planning application with real-time group trip collaboration. Plan trips through natural conversation, invite friends, and get intelligent travel recommendations in a shared chat room.

![AI Travel Planner](docs/image.png)

---

## Features

### AI Chat
- Conversational travel planning powered by **Google Gemini 2.5 Flash**
- Multi-agent **LangGraph** pipeline — weather, destination research, and itinerary planning run in parallel
- Streaming responses with live progress indicators
- Full conversation history with per-session context

### Group Trips
- Create trips and invite collaborators by email
- Real-time group chat over **WebSockets** — messages persist across sessions
- **Ambient Travel Agent** that passively listens to the group chat and responds only when a travel question needs answering
- Hard trigger via `@agent` for explicit questions
- Trip-scoped LangGraph memory — the agent remembers context within each trip separately

### Auth & Users
- JWT-based authentication (register / login)
- Email invitations for non-registered users — invitation link auto-joins them after sign-up

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Google Gemini 2.5 Flash |
| Agent framework | LangGraph + LangChain |
| Backend | FastAPI (async) |
| Database | PostgreSQL + SQLAlchemy (asyncpg) |
| Real-time | WebSockets (FastAPI native) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Observability | LangSmith tracing |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     Frontend (React)                 │
│  LoginPage  RegisterPage  ChatPage  TripChatArea     │
└────────────────────┬────────────────────────────────┘
                     │ HTTP + WebSocket (Vite proxy)
┌────────────────────▼────────────────────────────────┐
│                  FastAPI Backend                     │
│                                                      │
│  /auth      /chat/stream    /trips    /trips/{id}/ws │
└──────┬──────────────┬──────────────────┬────────────┘
       │              │                  │
  ┌────▼────┐   ┌─────▼──────┐   ┌──────▼────────┐
  │  Auth   │   │ LangGraph  │   │  WebSocket    │
  │  JWT    │   │  Pipeline  │   │  Room Manager │
  └─────────┘   └─────┬──────┘   └──────┬────────┘
                      │                  │
              ┌───────▼──────┐   ┌───────▼────────┐
              │  router      │   │ Trip Gatekeeper │
              │  extractor   │   │ (Gemini Flash)  │
              │  weather     │   └───────┬─────────┘
              │  info        │           │ YES
              │  planner     │   ┌───────▼─────────┐
              │  aggregator  │   │  LangGraph agent │
              └──────────────┘   │  thread_id=trip  │
                                 └─────────────────┘
```

### LangGraph Pipeline

```
user query
    │
    ▼
 router ──── chat? ──► chat_node ──► END
    │
  travel?
    │
    ▼
 extractor
    │
    ├──► weather_agent ──┐
    │                    ├──► planner_agent ──► aggregator ──► END
    └──► info_agent ─────┘
```

### Trip Agent (Hybrid Mode)

Every message in a trip room passes through a two-layer system:

1. **Gatekeeper** — fast Gemini Flash call reads last 50 messages and returns `{should_respond, question}`. Hard-bypassed if message contains `@agent`.
2. **Travel Agent** — full LangGraph pipeline invoked with trip chat context and a dedicated `thread_id` per trip. Response broadcast to all room members.

---

## Project Structure

```
mychatapp/
├── app/
│   ├── agents/
│   │   ├── graph.py              # LangGraph pipeline builder
│   │   ├── state.py              # TravelState TypedDict
│   │   ├── router.py             # Intent classifier + chat node
│   │   ├── extractor.py          # Travel detail extractor
│   │   ├── weather_agent.py      # OpenWeatherMap agent
│   │   ├── info_agent.py         # DuckDuckGo research agent
│   │   ├── planner_agent.py      # Itinerary planner
│   │   ├── aggregator.py         # Response formatter
│   │   └── trip_gatekeeper.py    # Group chat gatekeeper
│   ├── api/routes/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── trips.py
│   │   └── ws_trips.py           # WebSocket room endpoint
│   ├── models/
│   │   ├── user.py
│   │   ├── conversation.py
│   │   └── trip.py               # Trip, TripMember, TripMessage, TripInvitation
│   ├── services/
│   │   ├── chat_service.py
│   │   ├── trip_agent_service.py # Orchestrates gatekeeper → LangGraph → broadcast
│   │   └── email_service.py
│   ├── websocket/
│   │   └── manager.py            # In-memory room manager
│   └── core/
│       ├── config.py
│       ├── security.py
│       └── dependencies.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   └── ChatPage.jsx
│   │   ├── components/
│   │   │   ├── Sidebar.jsx
│   │   │   ├── ChatArea.jsx
│   │   │   ├── TripPanel.jsx
│   │   │   └── TripChatArea.jsx
│   │   ├── api/client.js
│   │   └── context/AuthContext.jsx
│   └── vite.config.js
├── cli.py                        # Terminal chat interface
├── requirements.txt
└── .env
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### 1. Clone & install backend

```bash
git clone <repo-url>
cd mychatapp
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

```env
GOOGLE_API_KEY=...
OPENWEATHER_API_KEY=...
JWT_SECRET_KEY=...
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/travel_planner
EMAIL_USER=your@gmail.com
EMAIL_PASSWORD=your_app_password
LANGCHAIN_API_KEY=...
```

### 3. Create the database

```sql
CREATE DATABASE travel_planner;
```

### 4. Start backend

```bash
uvicorn app.main:app --reload
```

Tables are auto-created on first startup.

### 5. Install & start frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## Environment Variables

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | Gemini API key |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens |
| `DATABASE_URL` | PostgreSQL asyncpg connection string |
| `EMAIL_USER` | Gmail address for sending invitations |
| `EMAIL_PASSWORD` | Gmail App Password |
| `LANGCHAIN_API_KEY` | LangSmith tracing key |
| `LANGCHAIN_PROJECT` | LangSmith project name |

---

## Usage

### Individual AI Chat
Type any travel query in the chat — the agent automatically routes between a quick conversational response and the full multi-agent planning pipeline.

### Group Trip Chat
1. Go to **Trips** tab → create a trip
2. Add members by email (registered users are added instantly; unregistered users receive an invitation email)
3. Click the chat icon on any trip to open the room
4. Chat with your group — the **Travel Agent** joins automatically when travel questions come up
5. Mention `@agent` anywhere to force a response

---

## CLI Interface

A terminal-based chat client is also available:

```bash
python cli.py
```

---

## License

MIT
