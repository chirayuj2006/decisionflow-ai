"""Local unit tests for DecisionFlow AI handler.

Run with:
    .venv\Scripts\python.exe -m pytest test_handler.py -v
or:
    .venv\Scripts\python.exe test_handler.py
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from handler import (
    DecisionFlowOutput,
    MeetingDecision,
    PendingDecision,
    ScopeChange,
    TimelineChange,
    _error_artifact,
    _extract_json,
    _parse_decision_flow_output,
    _render_markdown,
    handler,
)
from sitrep_agent.sdk import AgentInput, Ctx, LLM


class FakeLLM(LLM):
    def __init__(self, model: str = "fake-model", response: str = "") -> None:
        super().__init__(model=model)
        self.response = response
        self.calls: list[tuple[str, str]] = []

    async def complete(self, system: str, prompt: str, temperature: float = 0.7) -> str:
        self.calls.append((system, prompt))
        return self.response


def make_ctx(response: str = "") -> Ctx:
    return Ctx(
        instructions="",
        tools=[],
        llm=FakeLLM(model="fake-model", response=response),
        logs=[],
    )


def make_input(summary: str, task: dict[str, Any] | None = None) -> AgentInput:
    return AgentInput(
        task=task or {"title": "Test Report"},
        summary=summary,
        attendees=[],
        agent={},
    )


def test_extract_json_strips_fences() -> None:
    raw = '```json\n{"a": 1}\n```'
    assert _extract_json(raw) == '{"a": 1}'


def test_parse_valid_json() -> None:
    raw = """{
        "meeting_decisions": [{"decision": "Use Postgres", "status": "Approved"}],
        "scope_changes": [{"original_scope": "Web only", "changed_to": "Web + Mobile", "reason": "User demand"}],
        "pending_decisions": [{"decision_topic": "Cloud provider", "owner": "Bob"}],
        "risks_introduced": ["Tight deadline"],
        "timeline_changes": [{"original_timeline": "Q1", "updated_timeline": "Q2"}]
    }"""
    out = _parse_decision_flow_output(raw)
    assert out.meeting_decisions == [MeetingDecision("Use Postgres", "Approved")]
    assert out.scope_changes == [ScopeChange("Web only", "Web + Mobile", "User demand")]
    assert out.pending_decisions == [PendingDecision("Cloud provider", "Bob")]
    assert out.risks_introduced == ["Tight deadline"]
    assert out.timeline_changes == [TimelineChange("Q1", "Q2")]


def test_render_markdown() -> None:
    out = DecisionFlowOutput(
        meeting_decisions=[MeetingDecision("Use Postgres", "Approved")],
        scope_changes=[ScopeChange("Web only", "Web + Mobile", "User demand")],
        pending_decisions=[PendingDecision("Cloud provider", "Bob")],
        risks_introduced=["Tight deadline"],
        timeline_changes=[TimelineChange("Q1", "Q2")],
    )
    md = _render_markdown(out, "Sprint Review")
    assert "# Sprint Review" in md
    assert "Use Postgres" in md
    assert "Web + Mobile" in md
    assert "Cloud provider" in md
    assert "Tight deadline" in md
    assert "Q2" in md


def test_empty_transcript_returns_error() -> None:
    ctx = make_ctx()
    result = asyncio.run(handler(make_input(summary=""), ctx))
    assert result["artifacts"][0]["type"] == "markdown"
    assert "No meeting transcript" in result["artifacts"][0]["content"]


def test_invalid_json_returns_error() -> None:
    ctx = make_ctx(response="not valid json")
    result = asyncio.run(handler(make_input(summary="We decided to launch."), ctx))
    assert "Could not parse" in result["artifacts"][0]["content"]


def test_successful_run() -> None:
    response = """{
        "meeting_decisions": [{"decision": "Launch beta", "status": "Approved"}],
        "scope_changes": [],
        "pending_decisions": [],
        "risks_introduced": [],
        "timeline_changes": []
    }"""
    ctx = make_ctx(response=response)
    result = asyncio.run(handler(make_input(summary="We approved the beta launch."), ctx))
    content = result["artifacts"][0]["content"]
    assert "Launch beta" in content
    assert "Approved" in content


def test_error_artifact_shape() -> None:
    artifact = _error_artifact("Title", "Something went wrong")
    assert artifact["artifacts"][0]["type"] == "markdown"
    assert "Something went wrong" in artifact["artifacts"][0]["content"]


if __name__ == "__main__":
    test_extract_json_strips_fences()
    test_parse_valid_json()
    test_render_markdown()
    test_empty_transcript_returns_error()
    test_invalid_json_returns_error()
    test_successful_run()
    test_error_artifact_shape()
    print("All tests passed.")
