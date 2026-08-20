"""Hugging Face local LLM helpers for the ReAct Sherlock workshop."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"
MAX_NEW_TOKENS = 300
REACT_MAX_STEPS = 10

TOOL_DESCRIPTIONS = """
- query_server_logs(time_window): credentials that accessed servers in a 4-hour slot (e.g. "00:00-04:00", "20:00-00:00")
- check_badge_swipes(time): who is still badge-IN / on premises at HH:MM (e.g. "01:00")
- inspect_work_emails(employee_name): flagged keywords from recent work emails
- check_bank_records(employee_name): returns monthly wage, monthly deposit, monthly withdraw (numbers) and flagged transaction (string)
"""

KNOWN_TOOLS = (
    "query_server_logs",
    "check_badge_swipes",
    "inspect_work_emails",
    "check_bank_records",
)

REACT_FORMAT = """
Respond with exactly ONE of these formats per turn — never both.
Never invent Observations; wait for the next message after a tool call.

To use a tool (one call only, then STOP):
Thought: <your reasoning>
Action: <exact lowercase tool name>
Action Input: <plain string, e.g. 01:00 or 00:00-04:00 or Charlie>

When you have enough evidence from Observations already in the log:
Thought: <your final reasoning>
Final Answer: <suspect name only, e.g. Charlie>

Rules:
- Thought, then either Action + Action Input OR Final Answer — never both.
- After Action Input, stop. Do not write another Thought or Final Answer.
- Use exact tool names: query_server_logs, check_badge_swipes, inspect_work_emails, check_bank_records.
- Action Input must be a plain string, not JSON.
"""


@dataclass
class HFLocalLLM:
    model_id: str
    tokenizer: Any
    model: Any
    device: str

    def generate(self, system: str, user: str, max_new_tokens: int = MAX_NEW_TOKENS) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        output_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        new_tokens = output_ids[0, inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def load_llm(model_id: str = MODEL_ID, quiet: bool = False) -> HFLocalLLM:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise ImportError(
            "Install dependencies with: pip install torch transformers accelerate"
        ) from exc

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    try:
        model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype)
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(model_id, dtype=dtype)

    model = model.to(device).eval()

    if not quiet:
        print(f"Loaded {model_id} on {device} ({str(dtype).replace('torch.', '')})")

    return HFLocalLLM(model_id=model_id, tokenizer=tokenizer, model=model, device=device)


def format_suspects(case: Dict[str, Any]) -> str:
    lines = []
    for suspect in case["suspects"]:
        lines.append(
            f"- {suspect['name']} ({suspect['role']}): {suspect['profile']}"
        )
    return "\n".join(lines)


def build_watson_prompt(case: Dict[str, Any]) -> str:
    return (
        "You are Dr. Watson, a corporate investigator.\n"
        "You have ONLY the narrative profiles below. You cannot query logs, badges, "
        "emails, or bank records.\n\n"
        f"Incident: {case['incident']['summary']}\n"
        f"Time window: {case['incident']['time_window']}\n\n"
        "Suspects:\n"
        f"{format_suspects(case)}\n\n"
        "Who stole the algorithm? Reply in this format:\n"
        "Culprit: <name>\n"
        "Confidence: <low/medium/high>\n"
        "Reasoning: <2-3 sentences>"
    )


def parse_watson_response(text: str, suspects: List[str]) -> Dict[str, str]:
    culprit_match = re.search(r"Culprit:\s*(.+)", text, re.I)
    confidence_match = re.search(r"Confidence:\s*(.+)", text, re.I)
    reasoning_match = re.search(r"Reasoning:\s*(.+)", text, re.I | re.S)

    culprit = culprit_match.group(1).strip() if culprit_match else ""
    for name in suspects:
        if name.lower() in culprit.lower():
            culprit = name
            break
    if culprit not in suspects:
        culprit = suspects[0]

    return {
        "culprit": culprit,
        "confidence": (confidence_match.group(1).strip() if confidence_match else "unknown"),
        "explanation": (reasoning_match.group(1).strip() if reasoning_match else text.strip()),
        "raw_response": text,
    }


def watson_guess(case: Dict[str, Any], llm: HFLocalLLM) -> Dict[str, str]:
    system = "Answer concisely from the profiles only. Do not invent verified forensic evidence."
    user = build_watson_prompt(case)
    response = llm.generate(system, user)
    suspects = [s["name"] for s in case["suspects"]]
    return parse_watson_response(response, suspects)


def build_sherlock_system_prompt() -> str:
    return (
        "You are Sherlock Holmes, a ReAct investigator at Baskerville Tech.\n"
        "You must gather evidence with tools before accusing anyone.\n"
        "Each reply is one step only: Thought, then Action + Action Input "
        "(or Final Answer when done). Never both. Never invent Observations.\n"
        "Available tools:\n"
        f"{TOOL_DESCRIPTIONS}\n"
        f"{REACT_FORMAT}"
        "Start by checking who was active in the breach window, then cross-check "
        "badge swipes, emails, and bank records before accusing."
    )


def build_sherlock_user_prompt(case: Dict[str, Any], scratchpad: str) -> str:
    empty_log = (
        "(none yet — start with query_server_logs(\"00:00-04:00\"), "
        "the 4-hour slot covering the reported 00:30–02:00 theft window)"
    )
    log = scratchpad if scratchpad else empty_log
    return (
        f"Incident: {case['incident']['summary']}\n"
        f"Breach window: {case['incident']['time_window']}\n\n"
        "Suspects:\n"
        f"{format_suspects(case)}\n\n"
        "Investigation log so far:\n"
        f"{log}\n\n"
        "Reply with your next single step only "
        "(Thought + Action + Action Input, or Thought + Final Answer)."
    )


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


def _extract_field(text: str, field: str) -> Optional[str]:
    match = re.search(
        rf"{field}:\s*(.+?)(?=\n(?:Thought:|Action:|Action Input:|Final Answer:)|\Z)",
        text,
        re.I | re.S,
    )
    return match.group(1).strip() if match else None


def normalize_culprit(answer: str, suspects: List[str]) -> Optional[str]:
    answer_lower = answer.lower()
    for name in suspects:
        if name.lower() in answer_lower:
            return name
    return None


def run_react_agent(
    case: Dict[str, Any],
    tools: Dict[str, Callable[..., Any]],
    llm: HFLocalLLM,
    max_steps: int = REACT_MAX_STEPS,
) -> Dict[str, Any]:
    suspects = [s["name"] for s in case["suspects"]]
    system = build_sherlock_system_prompt()
    scratchpad = ""
    trace: List[Tuple[str, Optional[str], Optional[str], Any, str]] = []

    culprit: Optional[str] = None

    for _ in range(max_steps):
        user = build_sherlock_user_prompt(case, scratchpad)
        response = llm.generate(system, user)
        step = parse_react_step(response)

        thought = step.get("thought") or "Continuing investigation."
        final_answer = step.get("final_answer")
        action = step.get("action")
        action_input = step.get("action_input")

        if final_answer:
            culprit = normalize_culprit(final_answer, suspects) or final_answer
            trace.append((thought, None, None, {"final_answer": final_answer}, response))
            scratchpad += f"\nThought: {thought}\nFinal Answer: {final_answer}\n"
            break

        if not action or action not in tools:
            observation = {
                "error": f"Invalid or missing action: {action}. Use one of {list(tools)}."
            }
            trace.append((thought, action, action_input, observation, response))
            scratchpad += (
                f"\nThought: {thought}\nAction: {action}\nAction Input: {action_input}\n"
                f"Observation: {observation}\n"
            )
            continue

        try:
            observation = tools[action](action_input)
        except Exception as exc:  # noqa: BLE001 — show tool errors back to the model
            observation = {"error": str(exc)}

        trace.append((thought, action, action_input, observation, response))
        scratchpad += (
            f"\nThought: {thought}\nAction: {action}\nAction Input: {action_input}\n"
            f"Observation: {observation}\n"
        )

    if culprit is None:
        user = (
            build_sherlock_user_prompt(case, scratchpad)
            + "\n\nYou must now accuse exactly one suspect. Reply with Final Answer only."
        )
        response = llm.generate(system, user, max_new_tokens=120)
        step = parse_react_step(response)
        final_answer = step.get("final_answer") or response
        culprit = normalize_culprit(final_answer, suspects) or suspects[0]
        trace.append(("Forced final accusation.", None, None, {"final_answer": final_answer}, response))

    return {"culprit": culprit, "trace": trace, "scratchpad": scratchpad}
