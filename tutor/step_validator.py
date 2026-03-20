"""
Step validator for the step-by-step tutor.

Phase 1:
- SymPy-first equivalence checks for each step.
- If parsing fails and OpenAI is available, call OpenAI to judge.
"""

from __future__ import annotations

import json
import re
from typing import Any

from config import get_settings
from tutor.hint_system import generate_hint
from logger import get_logger

logger = get_logger()


_NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def _sympy_is_usable() -> bool:
    """
    Some environments have a partially installed SymPy (namespace package),
    which breaks parsing. We detect that and fall back to heuristics.
    """
    try:
        from sympy.parsing.sympy_parser import parse_expr  # type: ignore

        # Basic smoke test that exercises parsing.
        parse_expr("2+2", evaluate=True)
        return True
    except Exception:
        return False


def _normalize_for_compare(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("π", "pi").replace("Π", "pi")
    s = s.replace("×", "*").replace("·", "*").replace("−", "-").replace("–", "-")
    s = s.replace(" ", "")
    # Use '**' for exponent so we can compare user inputs consistently.
    s = s.replace("^", "**")
    # Insert implicit multiplication for common forms like `2x`.
    s = re.sub(r"(\d)\*?([a-zA-Z])", r"\1*\2", s)
    return s


def _try_linear_equation_value(step: str) -> float | None:
    """
    Extract x value from a simple equation like `5*x=45` or `x=9`.
    """
    s = (step or "").replace(" ", "")
    s = s.replace("^", "**")
    # x = number
    m = re.search(r"(?i)\bx\s*=\s*(" + _NUM_RE.pattern + r")", s)
    if m:
        return float(m.group(1))

    # a*x = b
    m = re.search(r"(?i)(" + _NUM_RE.pattern + r")\s*\*?\s*x\s*=\s*(" + _NUM_RE.pattern + r")", s)
    if m:
        a = float(m.group(1))
        b = float(m.group(2))
        if abs(a) < 1e-12:
            return None
        return b / a

    return None


def _normalize_math_string(s: str) -> str:
    s = (s or "").strip()
    s = s.replace("π", "pi").replace("Π", "pi")
    s = s.replace("×", "*").replace("·", "*")
    # Remove all whitespace to avoid SymPy parsing issues
    s = s.replace(" ", "")
    return s


def _normalize_text_step(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("π", "pi").replace("Π", "pi")
    s = s.replace("×", "*").replace("·", "*").replace("−", "-").replace("–", "-")
    s = s.replace("≥", ">=").replace("≤", "<=").replace("≠", "!=")
    s = s.replace("vertical asymptote", "va")
    s = s.replace("horizontal asymptote", "ha")
    s = s.replace("y-intercept", "yintercept")
    s = s.replace("not a function", "notafunction")
    s = s.replace("vertical scale/reflection by", "scale")
    s = s.replace("shift right", "shiftright")
    s = s.replace("shift left", "shiftleft")
    s = s.replace("shift up", "shiftup")
    s = s.replace("shift down", "shiftdown")
    s = s.replace("solution:", "")
    s = s.replace("domain:", "domain=")
    s = s.replace("quotient:", "quotient=")
    s = s.replace("remainder:", "remainder=")
    s = s.replace("factor:", "factor=")
    s = s.replace("vertex:", "vertex=")
    s = s.replace(" ", "")
    return s


def _looks_textual_step(step: str) -> bool:
    s = (step or "").lower()
    keywords = [
        "domain", "asymptote", "function", "quotient", "remainder", "factor", "vertex",
        "shift", "scale", "slope", "intercept", "log_", "composed", "f(", "g(",
        " or ", "<", ">", "interval", "growth", "decay",
    ]
    return any(k in s for k in keywords)


def _textual_step_equivalence(user_step: str, correct_step: str) -> bool:
    user_norm = _normalize_text_step(user_step)
    correct_norm = _normalize_text_step(correct_step)

    if user_norm == correct_norm:
        return True

    # Accept labeled equations like `m=2` vs `slope=2` after normalization.
    alias_pairs = [
        ("slope=", "m="),
        ("yintercept=", "b="),
        ("va=", "verticalasymptote="),
        ("ha=", "horizontalasymptote="),
    ]
    for a, b in alias_pairs:
        if user_norm.replace(a, b) == correct_norm.replace(a, b):
            return True

    # Allow `4` for `m=4` or `b=-3` style assignment steps.
    for labeled in ("m=", "b=", "remainder=", "factor=", "quotient=", "domain=", "va=", "ha=", "vertex="):
        if correct_norm.startswith(labeled) and user_norm == correct_norm[len(labeled) :]:
            return True

    # Allow user to enter only the simplified RHS of an equation step.
    # e.g. correct="log_5(5x)=1+log_5(x)", user="1+log_5(x)"
    if "=" in correct_norm:
        rhs = correct_norm.split("=", 1)[1]
        if user_norm == rhs:
            return True
        # Or just the final simplified expression on the RHS after the last =
        parts = correct_norm.split("=")
        if user_norm == parts[-1]:
            return True

    return False


def _extract_numeric_values(text: str) -> list[float]:
    values: list[float] = []
    for token in _NUM_RE.findall(text or ""):
        try:
            values.append(float(token))
        except Exception:
            continue
    return values


def _diagnose_mismatch(problem: dict, user_step: str, correct_step: str) -> tuple[str, str]:
    user_norm = _normalize_for_compare(user_step)
    correct_norm = _normalize_for_compare(correct_step)
    correct_text = _normalize_text_step(correct_step)
    problem_text = _normalize_text_step(str(problem.get("problem", "")))

    if _looks_textual_step(correct_step):
        if "notafunction" in correct_text:
            return ("function_rule", "A function cannot assign two different outputs to the same input value.")
        if correct_text.startswith("domain="):
            return ("domain_error", "Check which x-values must be excluded from the domain, especially denominator zeros.")
        if correct_text.startswith("va="):
            return ("vertical_asymptote_error", "The vertical asymptote should come from denominator zeros that do not cancel.")
        if correct_text.startswith("ha="):
            return ("horizontal_asymptote_error", "Check the degree comparison or leading coefficients for the horizontal asymptote.")
        if "shiftright" in correct_text or "shiftleft" in correct_text or "shiftup" in correct_text or "shiftdown" in correct_text or "scale" in correct_text:
            return ("transformation_error", "One or more graph transformation directions or magnitudes are off.")
        if "log_" in correct_text or "logbase" in problem_text:
            return ("log_rule_error", "Check the logarithm rule or exponential form you used in this step.")
        if "quotient=" in correct_text or "remainder=" in correct_text:
            return ("division_result_error", "The quotient or remainder does not match the polynomial division result.")
        if "factor=" in correct_text:
            return ("factor_sign_error", "Check the factor sign: a zero at c corresponds to the factor x-c.")
        if "vertex=" in correct_text:
            return ("vertex_error", "Check x = -b/(2a), then substitute that x-value back into the function.")
        if "f(" in correct_text:
            return ("function_evaluation_error", "Check which rule or expression should be applied to that input value.")
        if correct_text.startswith("m=") or correct_text.startswith("b="):
            return ("linear_feature_error", "Check whether you identified the slope or intercept from the function correctly.")
        if "<" in correct_text or ">" in correct_text or "or" in correct_text:
            return ("inequality_solution_error", "The inequality solution set or interval directions do not match the expected result.")

    user_has_eq = "=" in user_norm
    correct_has_eq = "=" in correct_norm
    if user_has_eq != correct_has_eq:
        return (
            "format_mismatch",
            "Your step format differs from the expected one. Use an equation when the expected step is an equation (or an expression when it is an expression).",
        )

    user_vals = _extract_numeric_values(user_norm)
    correct_vals = _extract_numeric_values(correct_norm)
    if len(user_vals) == len(correct_vals) and user_vals:
        user_abs = sorted(abs(v) for v in user_vals)
        correct_abs = sorted(abs(v) for v in correct_vals)
        if all(abs(a - b) < 1e-9 for a, b in zip(user_abs, correct_abs)):
            signs_differ = any((u < 0) != (c < 0) for u, c in zip(user_vals, correct_vals))
            if signs_differ:
                return ("sign_error", "There appears to be a sign error (+/-) in your transformation.")

    has_symbol = bool(re.search(r"[a-zA-Z]", user_norm + correct_norm))
    if not has_symbol:
        try:
            import sympy as sp

            u = _parse_with_sympy(user_step)
            c = _parse_with_sympy(correct_step)
            if sp.simplify(u - c) != 0:
                return (
                    "arithmetic_error",
                    "The arithmetic in this step is not equivalent to the expected result.",
                )
        except Exception:
            pass

    if user_has_eq and correct_has_eq:
        return (
            "equation_not_equivalent",
            "The equation is not equivalent to the expected next transformation.",
        )

    return (
        "not_equivalent",
        "This expression is not equivalent to the expected next transformation.",
    )


def _parse_with_sympy(expr: str) -> Any:
    import sympy as sp
    from sympy.parsing.sympy_parser import (
        convert_xor,
        implicit_multiplication_application,
        parse_expr,
        standard_transformations,
    )

    transform = standard_transformations + (implicit_multiplication_application, convert_xor)

    s = _normalize_math_string(expr)
    # Remove integration constant if present.
    s = re.sub(r"\b\+?\s*C\b", "", s, flags=re.IGNORECASE).strip()

    # Allow inputs like "x=4" by stripping leading variable assignment if needed.
    if "=" in s:
        parts = s.split("=", 1)
        # If lhs is just a symbol (like x), treat rhs as expression for equivalence.
        lhs = parts[0].strip()
        rhs = parts[1].strip()
        if re.fullmatch(r"[a-zA-Z]\w*", lhs):
            s = rhs

    return parse_expr(s, transformations=transform, evaluate=True)


def _equation_equivalence(user_step: str, correct_step: str) -> bool:
    """
    Compare two equations by checking equivalence of (lhs-rhs).
    """
    import sympy as sp
    from sympy.parsing.sympy_parser import (
        convert_xor,
        implicit_multiplication_application,
        parse_expr,
        standard_transformations,
    )

    transform = standard_transformations + (implicit_multiplication_application, convert_xor)

    def parse_side(s: str) -> sp.Expr:
        s = _normalize_math_string(s)
        s = re.sub(r"\b\+?\s*C\b", "", s, flags=re.IGNORECASE).strip()
        return parse_expr(s, transformations=transform, evaluate=True)

    if "=" not in user_step or "=" not in correct_step:
        return False

    u_parts = user_step.split("=", 1)
    c_parts = correct_step.split("=", 1)

    u_lhs, u_rhs = parse_side(u_parts[0]), parse_side(u_parts[1])
    c_lhs, c_rhs = parse_side(c_parts[0]), parse_side(c_parts[1])

    du = sp.simplify(u_lhs - u_rhs)
    dc = sp.simplify(c_lhs - c_rhs)
    return sp.simplify(du - dc) == 0


def is_step_correct(user_step: str, correct_step: str) -> bool:
    user_step = (user_step or "").strip()
    correct_step = (correct_step or "").strip()
    if not user_step:
        return False

    # Handle alternatives separated by " or " (e.g., "x = 3 or x = -3")
    if " or " in correct_step.lower():
        alternatives = [alt.strip() for alt in re.split(r"\s+or\s+", correct_step, flags=re.IGNORECASE)]
        for alt in alternatives:
            try:
                if is_step_correct(user_step, alt):
                    return True
            except Exception:
                pass
        # If we tried all alternatives and none matched, fall through to parse error
        raise ValueError(f"User step did not match any alternative in: {correct_step}")

    try:
        if not _sympy_is_usable():
            # Heuristic fallback when SymPy cannot parse at all.
            nu = _normalize_for_compare(user_step)
            nc = _normalize_for_compare(correct_step)
            if nu == nc:
                return True

            if _looks_textual_step(correct_step) and _textual_step_equivalence(user_step, correct_step):
                return True

            # Simple numeric checks for linear equations.
            ux = _try_linear_equation_value(user_step)
            cx = _try_linear_equation_value(correct_step)
            if ux is not None and cx is not None:
                return abs(ux - cx) < 1e-9

            # A couple of high-signal trig/identity cases from Phase 1 templates.
            if "sin(pi/6)" in nc and nu in {"1/2", "0.5", "sin(pi/6)"}:
                return True
            if "cos(pi/3)" in nc and nu in {"1/2", "0.5", "cos(pi/3)"}:
                return True
            if "sin(x)**2+cos(x)**2" in nu.replace(" ", "") and nc.replace(" ", "") in {"1", "1.0"}:
                return nu.replace(" ", "") == "1"

            return False

        if _looks_textual_step(correct_step) and _textual_step_equivalence(user_step, correct_step):
            return True

        # Prefer equation comparison if both look like equations.
        if "=" in user_step and "=" in correct_step:
            return _equation_equivalence(user_step, correct_step)

        # Expression equivalence.
        u_expr = _parse_with_sympy(user_step)
        c_expr = _parse_with_sympy(correct_step)

        import sympy as sp

        if (u_expr.is_Number or c_expr.is_Number) and u_expr == c_expr:
            return True

        return sp.simplify(u_expr - c_expr) == 0
    except Exception:
        # Parsing failed; caller can decide whether to use OpenAI fallback.
        raise


def get_progress_percentage(problem: dict, completed_steps: int) -> float:
    steps = list(problem.get("steps", []))
    if not steps:
        return 0.0
    pct = (max(0, completed_steps) / float(len(steps))) * 100.0
    return max(0.0, min(100.0, float(pct)))


def get_next_step_hint(problem: dict, current_step: int) -> str:
    # MVP hint strategy: use common mistakes list and keep it generic.
    common = list(problem.get("common_mistakes", []))
    wrong_step = ""  # placeholder; validate_step will provide the wrong step when needed.
    return generate_hint(common, wrong_step)


def _validate_with_openai(problem: dict, current_step: int, user_input: str) -> dict[str, Any]:
    """
    OpenAI fallback when SymPy parsing/comparison fails.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        return {"correct": False, "feedback": "I couldn't parse that step. Try rewriting it in standard math form.", "hint": None}

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)

    correct_step = problem.get("steps", [])[current_step]
    prompt = (
        "You are checking a student's step in solving:\n"
        f"{problem.get('problem','')}\n\n"
        f"The correct next step is: {correct_step}\n"
        f"Student wrote: {user_input}\n\n"
        "Is this step mathematically correct? Answer with JSON:\n"
        "{\"correct\": boolean, \"feedback\": \"explanation\", \"hint\": \"if wrong, give hint\"}"
    )

    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "Return only valid JSON for the requested schema."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content or "{}"
    return json.loads(content)


def validate_step(problem: dict, current_step: int, user_input: str) -> dict[str, Any]:
    """
    Validate a single user step against the expected next step.
    """
    steps = list(problem.get("steps", []))
    logger.info("Validate: step_idx=%d user_input='%s' (expected=%s)", current_step, user_input, steps[current_step] if 0 <= current_step < len(steps) else "(none)")
    
    if current_step < 0 or current_step >= len(steps):
        logger.warning("Validate: out of range step_idx=%d total_steps=%d", current_step, len(steps))
        return {
            "correct": False,
            "feedback": "No next step to validate.",
            "hint": None,
            "reason_code": "out_of_range",
            "reason": "There is no remaining step to check for this problem.",
        }

    correct_step = steps[current_step]
    try:
        correct = is_step_correct(user_input, correct_step)
        if correct:
            logger.info("Validate: CORRECT (step_idx=%d)", current_step)
            return {
                "correct": True,
                "feedback": "Correct. Good job—move to the next step.",
                "hint": None,
                "reason_code": "correct",
                "reason": "Your step is mathematically equivalent to the expected next transformation.",
            }

        logger.info("Validate: INCORRECT (step_idx=%d reason_code will follow)", current_step)
        hint = generate_hint(list(problem.get("common_mistakes", [])), user_input)
        reason_code, reason = _diagnose_mismatch(problem, user_input, correct_step)
        logger.info("Validate: reason_code=%s", reason_code)
        return {
            "correct": False,
            "feedback": "Not quite. Review the algebra and try the next transformation again.",
            "hint": hint,
            "reason_code": reason_code,
            "reason": reason,
        }
    except Exception as e:
        # SymPy couldn't parse/compare; optionally use OpenAI.
        logger.warning("Validate: SymPy failed (step_idx=%d): %s", current_step, repr(e), exc_info=False)
        try:
            openai_result = _validate_with_openai(problem=problem, current_step=current_step, user_input=user_input)
            correct = bool(openai_result.get("correct"))
            logger.info("Validate: OpenAI fallback correct=%s", correct)
            return {
                "correct": correct,
                "feedback": openai_result.get("feedback") or ("Correct." if correct else "Not quite."),
                "hint": openai_result.get("hint"),
                "reason_code": "openai_fallback_correct" if correct else "openai_fallback_incorrect",
                "reason": openai_result.get("feedback") or "OpenAI fallback was used because symbolic parsing failed.",
            }
        except Exception as e2:
            logger.error("Validate: Both SymPy and OpenAI failed: %s", repr(e2), exc_info=False)
            hint = generate_hint(list(problem.get("common_mistakes", [])), user_input)
            return {
                "correct": False,
                "feedback": "I couldn't parse that step reliably. Try rewriting it in simpler math notation (e.g., `2*x=8` or `x=4`).",
                "hint": hint,
                "reason_code": "parse_error",
                "reason": "The step couldn't be parsed reliably from the current notation.",
            }

