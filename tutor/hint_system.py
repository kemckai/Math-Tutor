"""
Hint generation (Phase 1).

For the MVP we use lightweight heuristics:
- If we recognize a common mistake keyword, return that guidance.
- Otherwise return a generic "match the expected algebra form" hint.
"""

from __future__ import annotations


def generate_hint(common_mistakes: list[str], wrong_step_text: str) -> str:
    wrong = (wrong_step_text or "").lower()

    if common_mistakes:
        # Try to choose the most relevant mistake message.
        for mistake in common_mistakes:
            m = (mistake or "").lower()
            if not m:
                continue
            # Very lightweight relevance check.
            if any(token in wrong for token in ["sign", "multiply", "divide", "factor", "subtract", "add", "square"]):
                return mistake

        # Default: use the first common mistake.
        return common_mistakes[0]

    return "Try to rewrite your step into the same algebraic form as the next expected transformation. Re-check arithmetic and signs."

