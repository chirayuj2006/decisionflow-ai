# DecisionFlow AI — Implementation Notes

## What was built

DecisionFlow AI is a SitRep remote agent that takes a meeting transcript and produces a structured Markdown report covering:

- ✅ Meeting Decisions
- 🔄 Scope Changes
- ⏳ Pending Decisions
- ⚠️ Risks Introduced
- 📅 Timeline Changes

## Files modified / created

| File | Change |
|------|--------|
| `handler.py` | Replaced the generic no-code handler with the full DecisionFlow AI implementation: system prompt, JSON schema, parsing, Markdown rendering, and error handling. |
| `agent.json` | Updated agent metadata (name, tagline, description, icon, color, task types). |
| `test_handler.py` | New file with local unit tests that exercise parsing, rendering, empty-input handling, invalid-JSON handling, and a successful end-to-end run using a fake LLM. |
| `IMPLEMENTATION.md` | This file. |

## How the LLM integration works

The starter kit's `sitrep_agent.sdk.LLM` class now loads `.env` via `python-dotenv` and reads from environment variables with **no hardcoded defaults**:

- `LLM_BASE_URL` — e.g. `https://openrouter.ai/api/v1`
- `MODEL` — e.g. `meta-llama/llama-3.1-8b-instruct:free`
- `LLM_API_KEY` — required for hosted providers

The handler calls `ctx.llm.complete(system=..., prompt=..., temperature=0.3)`.

To switch providers, just edit `.env` and restart the server.

## System prompt

The system prompt (`SYSTEM_PROMPT_DECISIONFLOW` in `handler.py`) instructs the model to return **only** a JSON object with these exact keys:

```json
{
  "meeting_decisions": [{"decision": "...", "status": "..."}],
  "scope_changes": [{"original_scope": "...", "changed_to": "...", "reason": "..."}],
  "pending_decisions": [{"decision_topic": "...", "owner": "..."}],
  "risks_introduced": ["..."],
  "timeline_changes": [{"original_timeline": "...", "updated_timeline": "..."}]
}
```

If a category has no relevant items, the model should return an empty array for that key.

## Parsing & Markdown formatting

1. `_extract_json()` strips any ` ```json ... ``` ` fences.
2. `_parse_decision_flow_output()` validates and parses the JSON into typed dataclasses.
3. `_render_markdown()` converts the dataclasses into a clean Markdown artifact with emoji section headings.

## Error handling

- **Empty transcript** — returns a Markdown artifact explaining that no transcript was provided.
- **LLM failure** — catches network/model errors and returns a Markdown artifact with the error message.
- **Invalid JSON** — catches `json.JSONDecodeError` and malformed responses, returning a Markdown artifact with the parse error.

## Local testing

Run the unit tests without needing an LLM:

```bash
cd "D:\BITS CSE\projects\kaggle_hack\sitrep-agent-starter"
.venv\Scripts\python.exe "D:\BITS CSE\projects\kaggle_hack\sitrep-agent-starter\test_handler.py"
```

Expected output:

```
All tests passed.
```

## Running the server

```bash
cd sitrep-agent-starter
.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 9002 --app-dir "D:\BITS CSE\projects\kaggle_hack\sitrep-agent-starter"
```

Health check:

```bash
curl http://localhost:9002/health
```

Test endpoint (requires a running LLM backend such as Ollama, or a hosted API key):

```bash
curl -X POST http://localhost:9002/test \
  -H "Content-Type: application/json" \
  -d '{"task":{"title":"DecisionFlow AI Report"},"summary":"Your meeting transcript here...","attendees":[],"agent":{}}'
```

## Next steps

1. Ensure an LLM backend is available (Ollama running locally, or set `LLM_BASE_URL` + `LLM_API_KEY` in `.env`).
2. Deploy the agent to SitRep Studio using the provided `render.yaml` / `Dockerfile`.
3. Optionally tune the system prompt or add more structured fields.
