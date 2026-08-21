"""Parsing / formatting helpers for the ReAct Sherlock workshop notebook."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

KNOWN_TOOLS = (
    "query_server_logs",
    "check_badge_swipes",
    "inspect_work_emails",
    "check_bank_records",
)


def format_suspects(case: Dict[str, Any]) -> str:
    lines = []
    for suspect in case["suspects"]:
        lines.append(
            f"- {suspect['name']} ({suspect['role']}): {suspect['profile']}"
        )
    return "\n".join(lines)


def _first_react_turn(text: str) -> str:
    """Keep only the first Thought → Action|Final Answer turn.

    Small models often hallucinate a second Thought/Final Answer in the same
    generation; those must not override the intended tool call.
    """
    text = text.strip()
    thought_matches = list(re.finditer(r"(?im)^Thought:", text))
    if len(thought_matches) < 2:
        return text

    first = text[: thought_matches[1].start()].strip()
    # Only truncate if the first turn already has a complete Action or Final Answer.
    if re.search(r"(?im)^(?:Action:|Final Answer:)", first):
        return first
    return text


def _normalize_action_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    lowered = name.strip().lower()
    for tool in KNOWN_TOOLS:
        if lowered == tool or lowered.replace("-", "_") == tool:
            return tool
    return lowered


def _normalize_action_input(action_input: Any) -> Any:
    """Coerce model outputs into the plain string tools expect."""
    if isinstance(action_input, dict):
        for key in ("employee_name", "time_window", "name", "input", "query"):
            if key in action_input and action_input[key] not in (None, ""):
                return str(action_input[key]).strip()
        if len(action_input) == 1:
            return str(next(iter(action_input.values()))).strip()
        return action_input

    if not isinstance(action_input, str):
        return action_input

    value = action_input.strip().strip("\"'")
    if value.startswith("{") or value.startswith("["):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        return _normalize_action_input(parsed)
    # Drop trailing junk / hallucinated follow-up lines.
    return value.splitlines()[0].strip()


def _extract_field(text: str, field: str) -> Optional[str]:
    match = re.search(
        rf"{field}:\s*(.+?)(?=\n(?:Thought:|Action:|Action Input:|Final Answer:)|\Z)",
        text,
        re.I | re.S,
    )
    return match.group(1).strip() if match else None


def parse_react_step(text: str) -> Dict[str, Optional[str]]:
    """Parse one ReAct step: Thought then Action, or Thought then Final Answer.

    If both Action and Final Answer appear, Action wins — the model must wait
    for an Observation before accusing.
    """
    turn = _first_react_turn(text)

    action_match = re.search(r"Action:\s*([A-Za-z_]+)", turn)
    inline_arg_match = re.search(
        r"Action:\s*[A-Za-z_]+\s*\(\s*[\"']?([^\"')\n]+)[\"']?\s*\)",
        turn,
    )
    action_input_match = re.search(
        r"Action Input:\s*(.+?)(?=\n(?:Thought:|Action:|Final Answer:)|\Z)",
        turn,
        re.I | re.S,
    )

    # Prefer Action over Final Answer whenever a tool call is present.
    if action_match:
        action_input: Any = None
        if action_input_match:
            action_input = action_input_match.group(1).strip()
        elif inline_arg_match:
            action_input = inline_arg_match.group(1).strip()

        return {
            "thought": _extract_field(turn, "Thought"),
            "final_answer": None,
            "action": _normalize_action_name(action_match.group(1)),
            "action_input": _normalize_action_input(action_input),
            "raw_response": text,
        }

    final_match = re.search(r"Final Answer:\s*(.+)", turn, re.I)
    if final_match:
        return {
            "thought": _extract_field(turn, "Thought"),
            "final_answer": final_match.group(1).strip().splitlines()[0].strip(),
            "action": None,
            "action_input": None,
            "raw_response": text,
        }

    return {
        "thought": _extract_field(turn, "Thought"),
        "final_answer": None,
        "action": None,
        "action_input": None,
        "raw_response": text,
    }


def normalize_culprit(answer: str, suspects: List[str]) -> Optional[str]:
    answer_lower = answer.lower()
    for name in suspects:
        if name.lower() in answer_lower:
            return name
    return None
