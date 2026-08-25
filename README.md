# Forge

> Multi-model app orchestration platform. Describe what you want to build — Forge routes each part of the job to the model best suited for it, with full transparency into what's happening and why.

[![CI](https://github.com/ghouseahmed226-debug/Forge/actions/workflows/ci.yml/badge.svg)](https://github.com/ghouseahmed226-debug/Forge/actions/workflows/ci.yml)

---

## What it does

1. You submit a prompt describing a website or app
2. Forge classifies the project type (static website vs. data-backed application)
3. Each subtask routes to the right model tier: fast models for scaffolding, strong reasoning models for business logic and security
4. A live routing trace shows you exactly which model is handling what, in real time
5. A mandatory critic pass reviews all security-sensitive code before anything ships
6. One-click deploy to Vercel (websites) or full stack (applications)

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI (Python 3.12), async |
| LLM Providers | Claude (Anthropic), GPT-4o (OpenAI), Gemini (Google) |
| Database | Supabase (Postgres + Row-Level Security) |
| Infra | Docker, GitHub Actions CI, Vercel |

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.12+
- Docker (for local full-stack dev)
- A [Supabase](https://supabase.com) project (free tier works)
- API keys for at least one LLM provider

### 1. Clone and configure

```bash
git clone https://github.com/ghouseahmed226-debug/Forge.git
cd Forge
cp .env.example .env
# Fill in all values in .env
```

### 2. Run the database migrations

In your Supabase dashboard → SQL Editor, run the contents of:
```
backend/db/migrations/001_initial.sql
```

### 3. Start with Docker Compose

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### 4. Start without Docker (development)

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
forge/
├── frontend/          # Next.js 14 App Router
├── backend/           # FastAPI application
│   ├── routers/       # API endpoints
│   ├── services/      # Business logic
│   │   ├── providers/ # LLM provider implementations
│   │   ├── router_engine.py
│   │   ├── critic.py
│   │   ├── quality_gates.py
│   │   ├── spend_guard.py
│   │   └── moderation.py
│   ├── db/            # Supabase client + migrations
│   └── tests/
├── .github/workflows/ # CI/CD
└── docker-compose.yml
```

## Routing Logic

| Task Type | Model Tier | Reason |
|---|---|---|
| UI scaffolding | Fast (Haiku / GPT-4o-mini / Gemini Flash) | High volume, low risk |
| Copy generation | Fast | Low risk; flagged for user review |
| Business logic | Reasoning (Opus / GPT-4o / Gemini Pro) | Correctness matters |
| Data models | Reasoning | Schema correctness critical |
| Security review | Reasoning + Critic pass | Never ships unreviewed |

## Running Tests

```bash
# Backend unit tests
cd backend
pytest tests/ -v -m "not integration"

# Backend integration tests (requires Supabase connection)
pytest tests/ -v -m integration

# Frontend type check
cd frontend
npx tsc --noEmit

# Frontend lint
npx eslint .
```

## Deployment

### Frontend (Vercel)

Connect your GitHub repo to Vercel. Set environment variables in Vercel dashboard:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL` (your backend URL)

### Backend

Deploy the Docker image to any container hosting (Railway, Fly.io, Cloud Run). Set all non-`NEXT_PUBLIC_` env vars as secrets.

## Security

- All LLM API keys are server-side only — never in the client bundle
- Per-user monthly spend caps enforced server-side
- Row-Level Security on all user data tables
- Prompt moderation before generation
- Critic pass on all security-sensitive generated code
- Rate limiting: 10 generation requests/hour per user

## License

MIT — see [LICENSE](LICENSE). You own the code Forge generates for you.
