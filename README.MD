# Agentic QA Fuzzer

An autonomous API fuzzing agent that uses an LLM to discover unhandled server exceptions in REST APIs. Unlike traditional fuzzers that rely on random or grammar-based input generation, this system reads the target's OpenAPI schema, understands validation boundaries, and iteratively mutates payloads to bypass input validation (422/400) and escalate to unhandled crashes (500). When it finds one, it writes a standalone pytest regression test.

## Architecture

This project is deployed using a decoupled, serverless architecture:
1. **Frontend (`docs/`)**: A static HTML/CSS/JS interface hosted on **GitHub Pages**.
2. **Backend (Cloud Run)**: A stateless FastAPI wrapper around a LangGraph agent. 

### How it works
1. You enter a target API URL into the GitHub Pages interface.
2. The frontend sends the URL to the Cloud Run backend.
3. The backend runs the AI agent. The agent proxies all HTTP requests through a Model Context Protocol (MCP) server subprocess (a sandbox).
4. If the agent crashes the target API (HTTP 500), the MCP server generates a Python regression test in temporary memory (`/tmp`).
5. The FastAPI backend reads the `.py` file and streams it directly back to the frontend as a downloadable file (no persistent storage or bucket costs!).

## Tech Stack
- **Backend API**: FastAPI, Uvicorn
- **AI Orchestration**: LangGraph, langchain-mcp-adapters
- **Tool Sandbox**: FastMCP
- **Frontend**: Vanilla HTML/JS, Glassmorphism CSS

## Deployment (Google Cloud Console)

1. Push this repository to GitHub.
2. Go to Google Cloud Console > **Cloud Run** > **Create Service**.
3. Select **Continuously deploy new revisions from a source repository**.
4. Connect your GitHub repo and select the root directory (where the `Dockerfile` lives).
5. Add your LLM API keys to the Cloud Run Environment Variables:
   - `LLM_PROVIDER` (e.g. `groq`, `gemini`, `openai`)
   - `GROQ_API_KEY`, `GEMINI_API_KEY`, or `OPENAI_API_KEY` depending on provider.
6. Once deployed, copy your Cloud Run URL and paste it into `docs/app.js` as the `API_BASE_URL`.
7. Enable GitHub Pages on the `docs/` folder of your repository.

## Guardrails
- **Recursion limit** — the LangGraph execution enforces a configurable `recursion_limit` to prevent runaway autonomous loops and bound token consumption.
- **Exception isolation** — every tool in `mcp_server.py` wraps its logic in try/except. A network timeout or target crash never kills the agent loop.
- **MCP process boundary** — the LLM reasoning layer has zero direct access to sockets. All side effects go through the MCP server subprocess.

## Local Development

Requires Python 3.10+.

```bash
# Clone and create virtual environment
git clone <repo-url> && cd agentic-qa-fuzzer
python -m venv .venv
.venv/Scripts/pip install -r fuzzer-agent/requirements.txt

# Set your API keys
echo LLM_PROVIDER=groq > .env
echo GROQ_API_KEY=your-key-here >> .env

# Run the backend locally
.venv/Scripts/uvicorn fuzzer-agent.src.api:app --reload --port 8080
```
Then, just open `docs/index.html` in your web browser!
