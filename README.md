# AI LinkedIn Post Agent

A professional-grade multi-agent AI system for creating high-quality, research-backed LinkedIn posts. Built with Django, React/TypeScript, Node.js gateway, PostgreSQL, and Redis.

## Architecture

```
Frontend (React/TS)  -->  Gateway (Node.js)  -->  Backend (Django)
   :3052                    :4052                    :8052
                              |                        |
                           WebSocket              Multi-Agent System
                           Redis PubSub           (LangGraph/LangChain)
                              |                        |
                           Redis :6452            PostgreSQL :5452
```

## Multi-Agent System

Ported from the Jupyter notebook, the system uses 5 specialized AI agents:

| Agent | Role |
|-------|------|
| **Supervisor** | Orchestrates workflow with deterministic-first routing + LLM fallback |
| **Researcher** | Searches web via Tavily API, summarizes findings (5-7 bullet points) |
| **Writer** | Creates/revises LinkedIn posts matching tone, audience, and word count |
| **Critic** | Evaluates drafts on 6 criteria: hook, clarity, value, structure, engagement, tone |
| **Evaluator** | Checks groundedness of claims against research (score 0-5) |

### Workflow: Supervisor -> Researcher -> Writer -> Critic -> (loop up to 5x) -> Evaluator

## Features

- **Multi-Agent Post Generation** - Research, write, critique, and evaluate in an automated pipeline
- **Real-time Progress** - WebSocket-based live agent step tracking
- **8 Post Templates** - Professional, Storytelling, Hot Take, How-To, Listicle, and more
- **7 Tone Presets** - Professional, Casual, Inspirational, Educational, Storytelling, Controversial, Humorous
- **Groundedness Evaluation** - Verifies claims against research with 0-5 scoring
- **Content Calendar** - Plan and schedule posts with recurring entries
- **Post History & Drafts** - Track all versions and critique feedback
- **MCP Server** - Model Context Protocol endpoints for tool integration
- **A2A Protocol** - Agent-to-Agent protocol for inter-agent communication
- **User Authentication** - JWT-based auth with multi-user support
- **Analytics Tracking** - Track impressions, likes, comments, shares

## Protocol Endpoints

### MCP (Model Context Protocol)
- `GET /mcp/manifest/` - Server capabilities
- `GET /mcp/tools/list/` - Available tools (generate, research, evaluate, critique, hashtags)
- `POST /mcp/tools/call/` - Execute a tool
- `GET /mcp/resources/list/` - Available resources

### A2A (Agent-to-Agent)
- `GET /a2a/agents/` - List all agent cards
- `GET /a2a/agents/{name}/` - Agent card
- `POST /a2a/agents/{name}/invoke/` - Invoke agent
- `GET /.well-known/agent.json` - A2A discovery

## Quick Start

```bash
# Clone and start all services
docker compose up --build

# Access the application
open http://172.168.1.95:3052

# Demo login: demo / demo1234
```

## Ports

| Service | Port |
|---------|------|
| Frontend | 3052 |
| Gateway (API + WebSocket) | 4052 |
| Backend (Django) | 8052 |
| PostgreSQL | 5452 |
| Redis | 6452 |

## Configuration

After logging in, go to **Settings** to configure:
1. OpenAI API Key (required)
2. Tavily API Key (required for web research)
3. Model selection (gpt-4o-mini default, gpt-4o for evaluation)
4. Custom OpenAI-compatible base URL

## Tech Stack

- **Backend**: Django 5.1, Django REST Framework, Celery, LangChain, LangGraph
- **Frontend**: React 18, TypeScript, Tailwind CSS, Zustand, Vite
- **Gateway**: Node.js, Express, WebSocket (ws), Redis pub/sub
- **Database**: PostgreSQL 16, Redis 7
- **Infrastructure**: Docker Compose
