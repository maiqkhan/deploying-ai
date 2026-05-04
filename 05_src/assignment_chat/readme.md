# ✈️ Travel Assistant
 
A conversational AI travel planning assistant built with Gradio, powered by an OpenAI-compatible LLM and three specialized services.
 
---
 
## Chat Client
 
The assistant has the personality of an enthusiastic travel companion — knowledgeable, practical, and conversational. It maintains memory throughout a session by passing the full conversation history to the agent on each turn.
 
Guardrails are applied at both the input and output level:
- Users cannot access, reveal, or modify the system prompt
- The assistant will not respond to questions about cats/dogs, horoscopes/zodiac signs, or Taylor Swift
---
 
## Services
 
### Service 1 — Weather API (`get_weather_api.py`)
Fetches live weather data from [Open-Meteo](https://open-meteo.com/) (free, no API key required) and returns a natural-language travel briefing via GPT. Raw JSON is never returned verbatim.
 
The service routes to one of three data sources depending on the travel date:
- **Today** → live current conditions
- **1–16 days out** → short-range forecast
- **17+ days out** → historical climate averages for that month (parallelized across 5 years using `ThreadPoolExecutor`)
Exposed as a FastAPI app on port `8001` and called by the agent as a `@tool`.
 
### Service 2 — Semantic Search (`search_destination` tool)
Answers destination questions using semantic search over a ChromaDB collection of Wikipedia city/country summaries.
 
**Dataset:** Wikipedia introductory articles for 24 major travel destinations, fetched via the Wikipedia REST API and stored in `data/articles.csv`.
 
**Embedding process:** Documents were embedded offline using OpenAI's `text-embedding-3-small` model via the course API gateway and stored in a file-persisted ChromaDB instance (`embeddings/chroma_db/`). The index is committed to the repository — no rebuilding is required at runtime.
 
> Note: ChromaDB uses SQLite as its internal storage engine. This is managed entirely by ChromaDB and is not a direct SQLite dependency of the application.
 
Retrieved passages are passed as context to GPT, which synthesises a grounded answer without hallucinating facts.
 
### Service 3 — MCP Tools (`mcp_server.py`)
A [FastMCP](https://github.com/jlowin/fastmcp) server exposing three function-calling tools over HTTP:
 
| Tool | Description |
|---|---|
| `currency_conversion` | Converts between 20 currencies using fixed reference rates |
| `calculate_trip_costs` | Estimates total trip cost from flights, accommodation, food, and activities |
| `time_zone_differences` | Returns current local times and hour offset between two IANA timezones |
 
The agent connects to this server via `MCPStreamableHTTPTool` and selects tools autonomously based on user intent.
 
---
 
## Implementation Decisions
 
**agent_framework over LangChain:** I used the `agent_framework` library was used for its simplicity. It provides a clean async context manager interface and native MCP support, which was sufficient for all assignment requirements.
 
**FastAPI for the weather service:** Wrapping the weather logic in FastAPI decouples it from the agent and makes it independently testable via `/docs`. It also allows the service to be called by other components without importing Python modules directly.
 
**File-persisted ChromaDB over Docker:** The `chromadb.PersistentClient` approach was chosen so the index can be committed to the repository and loaded at runtime without any setup steps. The pre-built index is included in `embeddings/chroma_db/`.
 
**Parallel HTTP requests for climate averages:** Fetching 5 years of historical weather data sequentially was too slow (~10s). `ThreadPoolExecutor` reduced this to the latency of a single request.
 
**Two-layer guardrails:** Input is checked with regex before reaching the agent (fast, no API cost). Output is checked after the agent responds to catch any accidental prompt leakage or persona hijacking.
 
---
 
## Running the Project
 
```bash
# 1. Install dependencies
uv sync
 
# 2. Set up environment variables
cp .env.example .env
# fill in API_GATEWAY_KEY
 
# 3. Start the MCP server (terminal 1)
python travel_typical_tasks.py
 
# 4. Start the weather API (terminal 2)
python get_weather_api.py
 
# 5. Start the Gradio app (terminal 3)
python travel_agent.py
```
 
Open `http://localhost:7860` in your browser.
 
---
 
## Project Structure
 
```
├── travel_agent.py                  # Gradio chat interface + agent
├── travel_typical_tasks.py           # FastMCP server (currency, costs, timezones)
├── get_weather_api.py      # FastAPI weather service
├── guardrails.py           # Input/output guardrail checks
├── utils.py                # OpenAI client helpers
├── embeddings/
│   ├── data/
│           └── articles.csv
│   ├── build_dataset.py    # Run once to build dataset csv
│   ├── build_index.py      # Run once to build ChromaDB index
│   └── chroma_db/          # Pre-built vector index (committed to repo)
└── .env.example