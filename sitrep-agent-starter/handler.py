"""DecisionFlow AI — Meeting Decision & Change Log Generator.

This agent receives a meeting transcript (via `input.summary`) and returns a
structured Markdown report containing:

  * meeting_decisions
  * scope_changes
  * pending_decisions
  * risks_introduced
  * timeline_changes

The LLM is instructed to emit strict JSON, which is parsed and rendered into a
clean Markdown artifact. Errors (empty transcript, invalid JSON, missing keys)
are handled gracefully and returned as Markdown artifacts with clear messages.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sitrep_agent.sdk import AgentInput, Ctx

# Fallback system prompt used when no Studio instructions are provided.
SYSTEM_PROMPT = Path(__file__).with_name("prompt.txt").read_text(encoding="utf-8").strip()


# ── Structured output schema ───────────────────────────────────────────

SYSTEM_PROMPT_DECISIONFLOW = """You are DecisionFlow AI, a meticulous meeting analyst.

Your job is to read the provided meeting transcript and produce a strict JSON object describing decisions made, scope changes, pending decisions, risks introduced, and timeline changes.

Return ONLY valid JSON. Do not include markdown code fences, explanations, or commentary outside the JSON object.

Use this exact structure:

{
  "meeting_decisions": [
    {"decision": "string", "status": "string"}
  ],
  "scope_changes": [
    {"original_scope": "string", "changed_to": "string", "reason": "string"}
  ],
  "pending_decisions": [
    {"decision_topic": "string", "owner": "string"}
  ],
  "risks_introduced": [
    "string"
  ],
  "timeline_changes": [
    {"original_timeline": "string", "updated_timeline": "string"}
  ]
}

Rules:
- If a category has no relevant items, return an empty array [] for that key.
- Keep text concise and factual. Do not invent information not present in the transcript.
- For status, prefer values like: Decided, Approved, Rejected, Deferred, Confirmed.
- For owners, use the person's name if known; otherwise use "TBD".
- For timeline_changes, include only changes explicitly discussed in the meeting.
""".strip()


# ── Data classes for the parsed LLM output ─────────────────────────────

@dataclass
class MeetingDecision:
    decision: str
    status: str


@dataclass
class ScopeChange:
    original_scope: str
    changed_to: str
    reason: str


@dataclass
class PendingDecision:
    decision_topic: str
    owner: str


@dataclass
class TimelineChange:
    original_timeline: str
    updated_timeline: str


@dataclass
class DecisionFlowOutput:
    meeting_decisions: list[MeetingDecision]
    scope_changes: list[ScopeChange]
    pending_decisions: list[PendingDecision]
    risks_introduced: list[str]
    timeline_changes: list[TimelineChange]


# ── Parsing helpers ────────────────────────────────────────────────────

def _extract_json(text: str) -> str:
    """Strip markdown fences and return the first JSON object found."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` blocks
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _get_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _parse_decision_flow_output(raw: str) -> DecisionFlowOutput:
    """Parse the LLM's JSON response into a typed DecisionFlowOutput."""
    cleaned = _extract_json(raw)
    if not cleaned:
        raise ValueError("LLM returned an empty response.")

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("LLM JSON must be an object.")

    meeting_decisions = [
        MeetingDecision(
            decision=_get_str(item.get("decision")),
            status=_get_str(item.get("status")),
        )
        for item in data.get("meeting_decisions", [])
        if isinstance(item, dict)
    ]

    scope_changes = [
        ScopeChange(
            original_scope=_get_str(item.get("original_scope")),
            changed_to=_get_str(item.get("changed_to")),
            reason=_get_str(item.get("reason")),
        )
        for item in data.get("scope_changes", [])
        if isinstance(item, dict)
    ]

    pending_decisions = [
        PendingDecision(
            decision_topic=_get_str(item.get("decision_topic")),
            owner=_get_str(item.get("owner"), "TBD"),
        )
        for item in data.get("pending_decisions", [])
        if isinstance(item, dict)
    ]

    risks_introduced = [
        _get_str(item)
        for item in data.get("risks_introduced", [])
        if item is not None
    ]

    timeline_changes = [
        TimelineChange(
            original_timeline=_get_str(item.get("original_timeline")),
            updated_timeline=_get_str(item.get("updated_timeline")),
        )
        for item in data.get("timeline_changes", [])
        if isinstance(item, dict)
    ]

    return DecisionFlowOutput(
        meeting_decisions=meeting_decisions,
        scope_changes=scope_changes,
        pending_decisions=pending_decisions,
        risks_introduced=risks_introduced,
        timeline_changes=timeline_changes,
    )


# ── Markdown renderer ──────────────────────────────────────────────────

def _render_markdown(output: DecisionFlowOutput, title: str) -> str:
    """Render a DecisionFlowOutput as clean Markdown."""
    lines: list[str] = [f"# {title}", ""]

    # Meeting decisions
    lines.append("## ✅ Meeting Decisions")
    if output.meeting_decisions:
        for item in output.meeting_decisions:
            lines.append(f"- **{item.decision}** — *Status: {item.status}*")
    else:
        lines.append("_No decisions recorded._")
    lines.append("")

    # Scope changes
    lines.append("## 🔄 Scope Changes")
    if output.scope_changes:
        for item in output.scope_changes:
            lines.append(
                f"- **{item.original_scope}** → **{item.changed_to}**"
            )
            if item.reason:
                lines.append(f"  - Reason: {item.reason}")
    else:
        lines.append("_No scope changes recorded._")
    lines.append("")

    # Pending decisions
    lines.append("## ⏳ Pending Decisions")
    if output.pending_decisions:
        for item in output.pending_decisions:
            lines.append(f"- **{item.decision_topic}** — Owner: {item.owner}")
    else:
        lines.append("_No pending decisions._")
    lines.append("")

    # Risks introduced
    lines.append("## ⚠️ Risks Introduced")
    if output.risks_introduced:
        for risk in output.risks_introduced:
            lines.append(f"- {risk}")
    else:
        lines.append("_No risks identified._")
    lines.append("")

    # Timeline changes
    lines.append("## 📅 Timeline Changes")
    if output.timeline_changes:
        for item in output.timeline_changes:
            lines.append(
                f"- **{item.original_timeline}** → **{item.updated_timeline}**"
            )
    else:
        lines.append("_No timeline changes recorded._")
    lines.append("")

    return "\n".join(lines)


def _error_artifact(title: str, message: str) -> dict:
    """Return a Markdown artifact describing an error."""
    return {
        "artifacts": [
            {
                "type": "markdown",
                "title": title,
                "content": f"# {title}\n\n⚠️ {message}\n",
            }
        ]
    }


# ── Main handler ───────────────────────────────────────────────────────

async def handler(input: AgentInput, ctx: Ctx) -> dict:
    task = input.task or {}
    title = task.get("title") or "DecisionFlow AI Report"
    transcript = (input.summary or "").strip()

    # Validate input
    if not transcript:
        ctx.log("empty transcript received")
        return _error_artifact(
            title,
            "No meeting transcript was provided. Please include a transcript and try again.",
        )

    # Build the prompt for the LLM
    system = SYSTEM_PROMPT_DECISIONFLOW
    if ctx.instructions.strip():
        # If the Studio provides custom instructions, prepend them but keep
        # the strict JSON schema requirement.
        system = f"{ctx.instructions.strip()}\n\n{SYSTEM_PROMPT_DECISIONFLOW}"

    user_prompt = (
        f"Analyze the following meeting transcript and return the required JSON structure.\n\n"
        f"Transcript:\n{transcript}"
    )

    ctx.log(f"DecisionFlow AI analyzing transcript with model={ctx.llm.model}")

    try:
        raw_llm_output = await ctx.llm.complete(
            system=system, prompt=user_prompt, temperature=0.3
        )
    except Exception as exc:
        ctx.log(f"llm error: {exc}")
        return _error_artifact(
            title,
            f"The language model failed to respond. Error: {exc}",
        )

    try:
        parsed = _parse_decision_flow_output(raw_llm_output)
    except ValueError as exc:
        ctx.log(f"parse error: {exc}")
        return _error_artifact(
            title,
            f"Could not parse the model response as valid JSON: {exc}",
        )

    markdown_content = _render_markdown(parsed, title)

    return {
        "artifacts": [
            {"type": "markdown", "title": title, "content": markdown_content},
        ]
    }
