# Voxora AI

**Conversational Business Intelligence Platform**

> Ask → Understand → Query → Analyse → Explain → Visualize → Continue

Voxora AI is a platform where users can speak or type natural-language questions and receive accurate answers, insights, charts, and dashboards from their organization's connected data.

## Architecture

```
voxora-frontend/    → Next.js 14+ (App Router, TypeScript, CSS Modules)
voxora-backend/     → FastAPI (Python 3.12+, SQLAlchemy, Async)
docker-compose.yml  → PostgreSQL 16 + Redis 7 (local dev)
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.12+
- Docker & Docker Compose

### 1. Start databases

```bash
docker compose up -d
```

### 2. Start the backend

```bash
cd voxora-backend
cp .env.example .env
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start the frontend

```bash
cd voxora-frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see Voxora.

## Core Experiences

| Experience | Description | Status |
|---|---|---|
| **Ask Voxora** | Conversational text/voice BI | ✅ Phase 1 |
| **Dashboards** | Traditional + AI-generated analytics | 🔜 Phase 4 |
| **Agent Studio** | Configure voice, behaviour, data access | 🔜 Phase 5 |

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14+, React 18, TypeScript, CSS Modules, Zustand |
| Backend | FastAPI, Python 3.12+, SQLAlchemy 2.0, Alembic |
| AI | OpenAI GPT-4o, Agents SDK |
| Voice | Web Speech API, Google Cloud STT/TTS |
| Database | PostgreSQL 16, Redis 7 |
| Data | Google BigQuery |
| Infra | Google Cloud (Cloud Run) |