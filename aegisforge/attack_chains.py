from __future__ import annotations

from dataclasses import dataclass

from .scanners.contracts import Finding


@dataclass(frozen=True)
class AttackChainCandidate:
    title: str
    finding_categories: list[str]
    severity: str
    priority: int


RULES = [
    (
        ["rag_poisoning", "prompt_injection", "tool_misuse"],
        "RAG poisoning to agent tool misuse",
        "high",
        90,
    ),
    (["prompt_injection", "tool_misuse"], "Prompt injection to tool misuse", "high", 80),
    (["llm_reachability", "prompt_injection"], "Reachable LLM with prompt-injection signal", "medium", 40),
]


def build_attack_chain_candidates(findings: list[Finding]) -> list[AttackChainCandidate]:
    categories = {finding.category for finding in findings}
    candidates: list[AttackChainCandidate] = []
    for required, title, severity, priority in RULES:
        if all(category in categories for category in required):
            candidates.append(AttackChainCandidate(title, required, severity, priority))
    return candidates
