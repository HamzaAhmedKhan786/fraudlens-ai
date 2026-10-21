import re

from fastapi import HTTPException

INJECTION_PATTERNS = (
    r"ignore (all|any|the) (previous|prior|system) instructions",
    r"reveal (the )?(system prompt|secret|api key|token)",
    r"act as (an? )?(administrator|system|developer)",
    r"override (the )?(risk|security|guardrail|policy)",
)


def validate_user_prompt(prompt: str) -> str:
    normalized = " ".join(prompt.split())
    if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in INJECTION_PATTERNS):
        raise HTTPException(400, "Prompt contains a prohibited instruction pattern")
    return normalized


def safe_evidence_value(value: object, limit: int = 4000) -> object:
    if isinstance(value, str):
        return value[:limit].replace("\x00", "")
    if isinstance(value, dict):
        return {str(k)[:100]: safe_evidence_value(v, limit) for k, v in list(value.items())[:100]}
    if isinstance(value, list):
        return [safe_evidence_value(item, limit) for item in value[:100]]
    return value


def ensure_grounded_answer(answer: str, allowed_citations: list[str]) -> str:
    if not answer.strip():
        raise HTTPException(502, "The configured model returned an empty response")
    cited = set(re.findall(r"\[([^\]]+)\]", answer))
    if allowed_citations and not cited:
        raise HTTPException(502, "The model response did not cite case evidence")
    if cited.difference(allowed_citations):
        raise HTTPException(502, "The model cited evidence outside this case")
    return answer[:12000]
