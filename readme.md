# DecisionFlow AI

SitRep Hackathon Submission (Code Track)

Rescue critical decisions from messy transcripts. Instantly generate a strict, actionable changelog of scope, risks, and timelines.

## The Business Problem

The biggest problem with AI in meetings today is fluffy, paragraph-long summaries. When an engineering team misses a timeline change because it was buried inside generated text, it costs the company real money.

DecisionFlow AI acts as a ruthless, automated project manager. It bypasses generic summarization and extracts a clean, structured changelog from messy, unstructured human conversations.

It outputs a highly scannable Markdown checklist containing five strict parameters:

- Approved Decisions
- Scope Changes
- Pending Items
- Risks Introduced
- Timeline Changes

## Technical Architecture

This agent was built for the Code Track to ensure maximum reliability and strict JSON outputs.

- **Backend:** Python & FastAPI
- **Intelligence:** OpenRouter API (`meta-llama/llama-3.1-8b-instruct`)
- **Integration:** SitRep webhooks via local SSH tunneling (ngrok / localhost.run)
- **Execution:** Heavily engineered system prompts to force the LLM to output pure JSON, bypassing conversational fluff

## Quickstart: Run it Locally

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory based on the example:

```bash
cp .env.example .env
```

Add your API keys to the `.env` file (e.g., your OpenRouter API key and your SitRep Agent Secret).

### 3. Run the Server

Start the local FastAPI server:

```bash
bash scripts/run-local.sh
```

This serves the app locally on port 9000.

### 4. Expose the Tunnel

In a new terminal window, expose your local server to the public web so SitRep can reach it:

```bash
bash scripts/tunnel.sh
```

Copy the generated `https://` URL and paste it into the **Endpoint URL** field in your SitRep Agent Studio.

## Testing the Agent

You can simulate a SitRep webhook payload directly to ensure the JSON extraction is working. While the server is running, execute:

```bash
bash scripts/smoke-test.sh
```

This will print the generated SitRep Markdown artifact directly in your terminal.
