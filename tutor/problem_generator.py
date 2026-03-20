"""
Problem generation + solution verification.

Phase 1 behavior:
- If `OPENAI_API_KEY` is set: call OpenAI to generate `problem`, `steps`, `answer`.
- Otherwise: use deterministic mock generation that still creates unique-ish problems.

Verification:
- Step-by-step validation is handled by `tutor.step_validator`.
- This module provides final answer/step equivalence checking with SymPy-first logic.
"""

from __future__ import annotations

import json
import random
import re
import uuid
from datetime import datetime
from typing import Any

from config import get_settings

from concepts.concept_library import get_concept_details

_NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def _normalize_math_string(s: str) -> str:
    s = s.strip()
    s = s.replace("π", "pi").replace("Π", "pi")
    s = s.replace("°", "")  # degrees not supported in Phase 1 mock generator
    # Common user formatting variants
    s = s.replace("×", "*").replace("·", "*")
    return s


def _extract_number_set(s: str) -> set[float]:
    s_norm = _normalize_math_string(s)
    nums = _NUM_RE.findall(s_norm)
    out: set[float] = set()
    for n in nums:
        try:
            out.add(float(n))
        except ValueError:
            pass
    return out


def _extract_xy_pair(s: str) -> tuple[float | None, float | None]:
    s_norm = _normalize_math_string(s).lower()
    x_val: float | None = None
    y_val: float | None = None

    # Look for x=... and y=...
    x_match = re.search(r"x\s*=\s*(" + _NUM_RE.pattern + r")", s_norm)
    if x_match:
        x_val = float(x_match.group(1))
    y_match = re.search(r"y\s*=\s*(" + _NUM_RE.pattern + r")", s_norm)
    if y_match:
        y_val = float(y_match.group(1))

    # Fallback: tuple parsing like (x,y)=(4,3)
    if x_val is None or y_val is None:
        pair = re.search(r"\(\s*x\s*,\s*y\s*\)\s*=\s*\(\s*(" + _NUM_RE.pattern + r")\s*,\s*(" + _NUM_RE.pattern + r")\s*\)", s_norm)
        if pair:
            x_val = float(pair.group(1))
            y_val = float(pair.group(2))
    return x_val, y_val


def generate_problem(concept: str, difficulty: str) -> dict[str, Any]:
    settings = get_settings()

    # Prefer concept metadata for common mistakes and for validating difficulty availability.
    concept_details = get_concept_details(concept)
    valid_difficulties = concept_details.get("available_difficulties", [])
    if difficulty not in valid_difficulties:
        difficulty = valid_difficulties[0] if valid_difficulties else difficulty

    if settings.openai_api_key:
        try:
            return _generate_problem_openai(concept=concept, difficulty=difficulty, concept_details=concept_details)
        except Exception:
            # If OpenAI fails, fall back to mock so the tutor remains usable.
            pass

    return _generate_problem_mock(concept=concept, difficulty=difficulty, concept_details=concept_details)


def _generate_problem_openai(concept: str, difficulty: str, concept_details: dict[str, Any]) -> dict[str, Any]:
    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    concept_text = concept_details["name"]
    description = concept_details["description"]

    system_prompt = "You are a math tutor creating practice problems."
    user_prompt = (
        f"Generate a {difficulty} level {concept_text} problem.\n"
        "Include:\n"
        "1. The problem statement\n"
        "2. Complete step-by-step solution (for validation)\n"
        "3. Final answer\n"
        "4. Common mistakes students make at each step\n\n"
        "Format as JSON with keys: problem, steps (array), answer, common_mistakes\n\n"
        f"Concept description: {description}"
    )

    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)

    return {
        "id": str(uuid.uuid4()),
        "concept_id": concept,
        "difficulty": difficulty,
        "problem": data["problem"],
        "steps": list(data["steps"]),
        "answer": data["answer"],
        "common_mistakes": list(data.get("common_mistakes", [])),
        "generated_at": datetime.utcnow().isoformat(),
        "source": "openai",
    }


def _generate_problem_mock(concept: str, difficulty: str, concept_details: dict[str, Any]) -> dict[str, Any]:
    """
    Deterministic but varied mock generator.
    Uses a seeded RNG so the same session/concept tends to create different problems.
    """
    seed_basis = f"{concept}:{difficulty}:{datetime.utcnow().date().isoformat()}"
    rng = random.Random(seed_basis)

    def pick_sample_common_mistakes() -> list[str]:
        for sp in concept_details.get("sample_problems", []):
            if sp.get("difficulty") == difficulty:
                return list(sp.get("common_mistakes", []))
        # fallback
        sp = (concept_details.get("sample_problems") or [{}])[0]
        return list(sp.get("common_mistakes", []))

    common_mistakes = pick_sample_common_mistakes()

    # Helper so steps are parseable and consistent (use '^' for power and omit unicode).
    def s_pow(base: int | str, exp: int | str) -> str:
        return f"({base})^{exp}"

    def fmt_num(v: float) -> str:
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return f"{v:.4f}".rstrip("0").rstrip(".")

    # New concept templates imported from Math Grimoire.
    if concept == "applied_simple_interest":
        if difficulty == "beginner":
            P = rng.choice([500, 800, 1000])
            r = rng.choice([0.04, 0.05])
            t = rng.choice([1, 2])
        elif difficulty == "intermediate":
            P = rng.choice([1000, 1200, 1500, 2000])
            r = rng.choice([0.03, 0.04, 0.05, 0.06])
            t = rng.choice([2, 3, 4, 5])
        else:  # advanced
            P = rng.choice([2000, 2500, 3500, 5000])
            r = rng.choice([0.025, 0.035, 0.045, 0.065, 0.075])
            t = rng.choice([3, 5, 7, 10])
        I = round(P * r * t, 2)
        A = round(P + I, 2)
        problem_text = f"Simple interest: P={P}, r={r}, t={t}. Find I and A."
        steps = [
            f"I = {P}*{r}*{t}",
            f"I = {fmt_num(I)}",
            f"A = {P} + {fmt_num(I)}",
            f"A = {fmt_num(A)}",
        ]
        answer = f"I={fmt_num(I)}, A={fmt_num(A)}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "applied_compound_interest":
        if difficulty == "beginner":
            P = rng.choice([1000, 1200])
            r = rng.choice([0.04, 0.05])
            n = 1
            t = rng.choice([1, 2])
        elif difficulty == "intermediate":
            P = rng.choice([1000, 1500, 2000])
            r = rng.choice([0.03, 0.04, 0.05, 0.06])
            n = rng.choice([2, 4])
            t = rng.choice([2, 3, 5])
        else:  # advanced
            P = rng.choice([2000, 3000, 5000])
            r = rng.choice([0.03, 0.05, 0.08])
            n = 12
            t = rng.choice([5, 8, 10])
        A = round(P * ((1 + r / n) ** (n * t)), 2)
        problem_text = f"Compound interest: P={P}, r={r}, n={n}, t={t}. Find A."
        steps = [
            f"A = {P}*(1+{r}/{n})^({n}*{t})",
            f"A = {fmt_num(A)}",
        ]
        answer = fmt_num(A)
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "applied_distance_rate_time":
        if difficulty == "beginner":
            # Find rate only, integer results
            pairs = [(60,2),(90,3),(120,4),(80,2),(150,3)]
            d, t_val = rng.choice(pairs)
            r = d // t_val
            problem_text = f"Travel {d} miles in {t_val} hours. Find rate r."
            steps = [f"r = {d}/{t_val}", f"r = {fmt_num(r)}"]
            answer = fmt_num(r)
        elif difficulty == "intermediate":
            mode = rng.choice(["find_rate", "find_time"])
            if mode == "find_rate":
                d = rng.choice([90, 120, 180, 240, 300])
                t_val = rng.choice([1.5, 2, 3, 4, 5])
                r = d / t_val
                problem_text = f"Travel {d} miles in {t_val} hours. Find rate r."
                steps = [f"r = {d}/{t_val}", f"r = {fmt_num(r)}"]
                answer = fmt_num(r)
            else:
                d = rng.choice([120, 150, 240, 300])
                r = rng.choice([30, 40, 50, 60])
                t_val = d / r
                problem_text = f"Travel {d} miles at {r} mph. Find time t."
                steps = [f"t = {d}/{r}", f"t = {fmt_num(t_val)}"]
                answer = fmt_num(t_val)
        else:  # advanced
            mode = rng.choice(["find_rate", "find_time", "find_distance"])
            if mode == "find_rate":
                d = rng.choice([350, 420, 480, 520, 630])
                t_val = rng.choice([3.5, 4.5, 5.5, 6, 7])
                r = round(d / t_val, 4)
                problem_text = f"A train covers {d} miles in {t_val} hours. Find average speed r."
                steps = [f"r = {d}/{t_val}", f"r = {fmt_num(r)}"]
                answer = fmt_num(r)
            elif mode == "find_time":
                d = rng.choice([420, 480, 525, 600, 700])
                r = rng.choice([35, 42, 50, 60, 70])
                t_val = round(d / r, 4)
                problem_text = f"A car travels {d} miles at {r} mph. Find time t."
                steps = [f"t = {d}/{r}", f"t = {fmt_num(t_val)}"]
                answer = fmt_num(t_val)
            else:
                r = rng.choice([45, 55, 60, 65, 75])
                t_val = rng.choice([2.5, 3, 3.5, 4, 4.5])
                d = round(r * t_val, 2)
                problem_text = f"A vehicle travels at {r} mph for {t_val} hours. Find distance d."
                steps = [f"d = {r}*{t_val}", f"d = {fmt_num(d)}"]
                answer = fmt_num(d)
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "applied_mixture":
        if difficulty == "beginner":
            q1 = q2 = 2
            c1 = rng.choice([0.25, 0.50])
            c2 = rng.choice([0.75, 1.0])
        elif difficulty == "intermediate":
            q1 = rng.choice([2, 3, 4])
            q2 = rng.choice([2, 3, 4])
            c1 = rng.choice([0.2, 0.25, 0.3, 0.35])
            c2 = rng.choice([0.45, 0.5, 0.55, 0.6])
        else:  # advanced
            q1 = rng.choice([5, 6, 8, 10])
            q2 = rng.choice([4, 5, 6, 8])
            c1 = rng.choice([0.15, 0.20, 0.30, 0.35, 0.40])
            c2 = rng.choice([0.50, 0.55, 0.60, 0.65, 0.70])
        acid = round(c1 * q1 + c2 * q2, 4)
        total = q1 + q2
        final_c = round(acid / total, 4)
        problem_text = f"Mix {q1} L of {c1*100:.0f}% with {q2} L of {c2*100:.0f}%. Find final concentration."
        steps = [
            f"acid = {c1}*{q1} + {c2}*{q2}",
            f"acid = {fmt_num(acid)}",
            f"c = {fmt_num(acid)}/{total}",
            f"c = {fmt_num(final_c)}",
        ]
        answer = fmt_num(final_c)
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_linear_two_variables":
        if difficulty == "beginner":
            a = rng.choice([1, 2])
            b = rng.choice([1, 2, 4])
            c = rng.choice([4, 6, 8])
        elif difficulty == "intermediate":
            a = rng.choice([1, 2, 3, 4, 5])
            b = rng.choice([2, 3, 4, 5, 6])
            c = rng.choice([6, 8, 10, 12, 15])
        else:  # advanced
            a = rng.choice([3, 4, 5, 6, 7])
            b = rng.choice([2, 3, 5, 6, 7])
            c = rng.choice([12, 15, 18, 20, 24])
        problem_text = f"Rewrite {a}x + {b}y = {c} in slope-intercept form."
        steps = [f"{b}*y = -{a}*x + {c}", f"y = (-{a}/{b})*x + ({c}/{b})"]
        answer = f"y = (-{a}/{b})*x + ({c}/{b})"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_linear_functions":
        if difficulty == "beginner":
            m = rng.choice([1, 2, -1, -2])
            b = rng.choice([0, 1, 2, -1, -2])
        elif difficulty == "intermediate":
            m = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4])
            b = rng.choice([-6, -4, -2, 0, 2, 3, 5])
        else:  # advanced
            m = rng.choice([-7, -5, -3, 3, 5, 7])
            b = rng.choice([-10, -8, -6, 6, 8, 10])
        problem_text = f"For f(x)={m}*x+({b}), identify slope and y-intercept."
        steps = [f"m = {m}", f"b = {b}"]
        answer = f"slope={m}, y-intercept={b}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_rational_equations":
        if difficulty == "beginner":
            k = rng.choice([1, 2])
            c = rng.choice([2, 3, 4])
            rhs = rng.choice([2, 3, 4])
        elif difficulty == "intermediate":
            k = rng.choice([1, 2, 3, 4])
            c = rng.choice([2, 3, 4, 5, 6])
            rhs = rng.choice([3, 4, 5, 6, 7])
        else:  # advanced
            k = rng.choice([-5, -4, -3, -2, 4, 5, 6])
            c = rng.choice([3, 4, 5, 6, 7, 8])
            rhs = rng.choice([4, 5, 6, 7, 8])
        num = rhs * c
        x = c + k
        problem_text = f"Solve {num}/(x-({k})) = {rhs}."
        steps = [f"{num} = {rhs}*(x-({k}))", f"x-({k}) = {c}", f"x = {x}"]
        answer = f"x={x}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_absolute_value_equations":
        if difficulty == "beginner":
            h = 0
            k = rng.choice([1, 2, 3])
        elif difficulty == "intermediate":
            h = rng.choice([-3, -1, 0, 2, 4])
            k = rng.choice([1, 2, 3, 4, 5])
        else:  # advanced
            h = rng.choice([-8, -6, -5, -4, 4, 5, 6, 8])
            k = rng.choice([3, 4, 5, 6, 7])
        x1 = h + k
        x2 = h - k
        problem_text = f"Solve |x-({h})| = {k}."
        steps = [f"x-({h}) = {k} or x-({h}) = -{k}", f"x = {x1} or x = {x2}"]
        answer = f"x={x1} or x={x2}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_absolute_value_inequalities":
        if difficulty == "beginner":
            h = 0
            k = rng.choice([1, 2, 3])
            less_than = True  # always bounded ("and" form)
        elif difficulty == "intermediate":
            h = rng.choice([-4, -2, 0, 1, 3])
            k = rng.choice([1, 2, 3, 4])
            less_than = rng.choice([True, False])
        else:  # advanced
            h = rng.choice([-6, -5, -4, 4, 5, 6])
            k = rng.choice([3, 4, 5, 6])
            less_than = rng.choice([True, False])
        left = h - k
        right = h + k
        if less_than:
            problem_text = f"Solve |x-({h})| < {k}."
            steps = [f"-{k} < x-({h}) < {k}", f"{left} < x < {right}"]
            answer = f"{left} < x < {right}"
        else:
            problem_text = f"Solve |x-({h})| > {k}."
            steps = [f"x-({h}) < -{k} or x-({h}) > {k}", f"x < {left} or x > {right}"]
            answer = f"x<{left} or x>{right}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_function_composition":
        if difficulty == "beginner":
            # f(x)=x^2, g(x)=x+a (simple)
            a = rng.choice([1, 2, 3])
            problem_text = f"If f(x)=x^2 and g(x)=x+{a}, find f(g(x))."
            steps = [f"f(g(x)) = (x+{a})^2", f"f(g(x)) = x^2 + {2*a}*x + {a*a}"]
            answer = f"x^2 + {2*a}*x + {a*a}"
        elif difficulty == "intermediate":
            # f(x)=x+a, g(x)=x^2  →  f(g(x))=x^2+a
            a = rng.choice([2, 3, 4, 5])
            problem_text = f"If f(x)=x+{a} and g(x)=x^2, find f(g(x))."
            steps = [f"f(g(x)) = (x^2)+{a}", f"f(g(x)) = x^2 + {a}"]
            answer = f"x^2 + {a}"
        else:  # advanced
            # f(x)=2x+a, g(x)=x^2+b  →  f(g(x))=2*(x^2+b)+a=2x^2+(2b+a)
            a = rng.choice([1, 2, 3, 4])
            b = rng.choice([1, 2, 3, 4])
            c = 2 * b + a
            problem_text = f"If f(x)=2x+{a} and g(x)=x^2+{b}, find f(g(x))."
            steps = [f"f(g(x)) = 2*(x^2+{b})+{a}", f"f(g(x)) = 2*x^2 + {c}"]
            answer = f"2*x^2 + {c}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_function_operations":
        a = rng.choice([1, 2, 3, 4])
        if difficulty == "beginner":
            op = "add"
            problem_text = f"Given f(x)=x^2 and g(x)=x+{a}, find (f+g)(x)."
            steps = [f"(f+g)(x) = x^2 + (x+{a})", f"(f+g)(x) = x^2 + x + {a}"]
            answer = f"x^2 + x + {a}"
        elif difficulty == "intermediate":
            b = rng.choice([1, 2, 3, 4])
            op = rng.choice(["subtract", "multiply"])
            if op == "subtract":
                problem_text = f"Given f(x)=x^2+{a} and g(x)=x+{b}, find (f-g)(x)."
                steps = [f"(f-g)(x) = (x^2+{a}) - (x+{b})", f"(f-g)(x) = x^2 - x + {a-b}"]
                answer = f"x^2 - x + {a-b}"
            else:
                problem_text = f"Given f(x)=x+{a} and g(x)=x+{b}, find (f*g)(x)."
                c2 = a + b
                c0 = a * b
                steps = [f"(f*g)(x) = (x+{a})*(x+{b})", f"(f*g)(x) = x^2 + {c2}*x + {c0}"]
                answer = f"x^2 + {c2}*x + {c0}"
        else:  # advanced
            b = rng.choice([1, 2, 3, 4])
            problem_text = f"Given f(x)=x^2+{a} and g(x)=x+{b}, find all four operations (f+g), (f-g), (f*g), (f/g)."
            fg_add = f"x^2 + x + {a+b}"
            fg_sub = f"x^2 - x + {a-b}"
            fg_mul_c = a + b
            fg_mul_c0 = a * b
            fg_mul = f"x^3 + {fg_mul_c}*x^2 + {fg_mul_c0}*x + ... "
            steps = [
                f"(f+g)(x) = {fg_add}",
                f"(f-g)(x) = {fg_sub}",
                f"(f*g)(x) = (x^2+{a})*(x+{b})",
                f"(f/g)(x) = (x^2+{a})/(x+{b})",
            ]
            answer = f"(f+g)={fg_add}; (f-g)={fg_sub}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_functions_relations":
        if difficulty == "beginner":
            # Obviously not a function (same x, adjacent y values)
            dup_x = rng.choice([1, 2, 3])
            y1, y2 = 1, 2
            other_x = dup_x + 2
            other_y = 3
            is_func = False
        elif difficulty == "intermediate":
            if rng.choice([True, False]):
                # Not a function
                dup_x = rng.choice([1, 2, 3, 4])
                y1, y2 = rng.sample([2, 3, 4, 5, 6], 2)
                other_x = dup_x + rng.choice([2, 3, 4])
                other_y = rng.choice([1, 2, 3, 4, 5])
                is_func = False
            else:
                # Is a function (all unique x)
                xs = rng.sample([1, 2, 3, 4, 5, 6], 3)
                ys = rng.sample([1, 2, 3, 4, 5, 6], 3)
                dup_x = xs[0]; y1 = ys[0]; y2 = ys[1]; other_x = xs[1]; other_y = ys[2]
                # We'll use (xs[0],ys[0]),(xs[1],ys[1]),(xs[2],ys[2]) — all unique x
                other_x2 = xs[2]; other_y2 = ys[2]
                is_func = True
        else:  # advanced — 5-pair set, student must check all x values
            is_func = rng.choice([True, False])
            if not is_func:
                dup_x = rng.choice([1, 2, 3, 4])
                y1, y2 = rng.sample([1, 2, 3, 4, 5], 2)
                other_x = dup_x + 2; other_y = rng.choice([1, 2, 3])
            else:
                xs = rng.sample(range(1, 8), 3)
                ys = rng.sample(range(1, 8), 3)
                dup_x = xs[0]; y1 = ys[0]; y2 = ys[1]; other_x = xs[1]; other_y = ys[2]
        if not is_func:
            problem_text = f"Is {{({dup_x},{y1}), ({dup_x},{y2}), ({other_x},{other_y})}} a function?"
            steps = [f"x = {dup_x} has two outputs", "not a function"]
            answer = "Not a function"
        else:
            problem_text = f"Is {{({dup_x},{y1}), ({other_x},{other_y})}} a function?"
            steps = ["each x has exactly one output", "is a function"]
            answer = "Is a function"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_complex_numbers":
        if difficulty == "beginner":
            # Addition only
            a, b = rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
            c, d = rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
            problem_text = f"Add ({a}+{b}i) + ({c}+{d}i)."
            steps = [f"real: {a}+{c} = {a+c}", f"imag: {b}+{d} = {b+d}", f"= {a+c}+{b+d}*i"]
            answer = f"{a+c}+{b+d}*i"
        elif difficulty == "intermediate":
            # Multiplication with small values
            a, b = rng.choice([1, 2, 3, 4]), rng.choice([1, 2, 3, 4])
            c, d = rng.choice([1, 2, 3, 4]), rng.choice([-3, -2, -1, 1, 2, 3])
            real = a * c - b * d
            imag = a * d + b * c
            problem_text = f"Multiply ({a}+{b}i)({c}+({d})i)."
            steps = [f"= {a*c} + {a*d}*i + {b*c}*i + {b*d}*i^2", f"= {real} + {imag}*i"]
            answer = f"{real}+{imag}*i"
        else:  # advanced — division by conjugate
            a, b = rng.choice([2, 3, 4, 5]), rng.choice([1, 2, 3, 4])
            c, d = rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
            denom = c * c + d * d
            num_real = a * c + b * d
            num_imag = b * c - a * d
            problem_text = f"Divide ({a}+{b}i) / ({c}+{d}i). Multiply by conjugate."
            steps = [
                f"multiply by ({c}-{d}i)/({c}-{d}i)",
                f"numerator: ({a}+{b}i)({c}-{d}i) = {num_real} + {num_imag}*i",
                f"denominator: {c}^2+{d}^2 = {denom}",
                f"= {fmt_num(num_real/denom)} + {fmt_num(num_imag/denom)}*i",
            ]
            answer = f"{fmt_num(num_real/denom)}+{fmt_num(num_imag/denom)}*i"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_quadratic_functions":
        if difficulty == "beginner":
            a = 1
            h = rng.choice([-2, -1, 0, 1, 2])
            k = rng.choice([-2, 0, 1, 2, 3])
        elif difficulty == "intermediate":
            a = rng.choice([1, 2, 3])
            h = rng.choice([-3, -2, -1, 0, 1, 2, 3])
            k = rng.choice([-4, -2, 0, 2, 4])
        else:  # advanced
            a = rng.choice([-3, -2, -1, 2, 3])
            h = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5])
            k = rng.choice([-6, -4, -2, 4, 6, 8])
        b = -2 * a * h
        c = a * h * h + k
        problem_text = f"Find the vertex of f(x)={a}*x^2 + ({b})*x + ({c})."
        steps = [f"x = -({b})/(2*{a})", f"x = {h}", f"f({h}) = {k}", f"vertex = ({h},{k})"]
        answer = f"({h},{k})"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_polynomial_division":
        if difficulty == "beginner":
            # degree-2 dividend / linear divisor, zero remainder
            r = rng.choice([1, 2, 3])
            q0 = rng.choice([1, 2, 3, 4])
            a1 = q0 - r  # coefficient of x in dividend
            a0 = -r * q0
            problem_text = f"Divide x^2 + ({a1})*x + ({a0}) by x-({r})."
            steps = [f"quotient = x + ({q0})", "remainder = 0"]
            answer = f"x + ({q0}) with remainder 0"
        elif difficulty == "intermediate":
            # degree-3 / linear, zero remainder
            r = rng.choice([1, 2, 3, 4])
            q1 = rng.choice([1, 2, 3, 4])
            q0 = rng.choice([-2, -1, 1, 2, 3, 4])
            rem = 0
            a2 = q1 - r
            a1 = q0 - r * q1
            a0 = -r * q0
            problem_text = f"Divide x^3 + ({a2})*x^2 + ({a1})*x + ({a0}) by x-({r})."
            steps = [f"quotient = x^2 + ({q1})*x + ({q0})", f"remainder = {rem}"]
            answer = f"x^2 + ({q1})*x + ({q0}) with remainder {rem}"
        else:  # advanced — nonzero remainder
            r = rng.choice([1, 2, 3, 4])
            q1 = rng.choice([1, 2, 3, 4])
            q0 = rng.choice([-2, -1, 1, 2, 3, 4])
            rem = rng.choice([1, 2, 3, 4, 5])
            a2 = q1 - r
            a1 = q0 - r * q1
            a0 = rem - r * q0
            problem_text = f"Divide x^3 + ({a2})*x^2 + ({a1})*x + ({a0}) by x-({r})."
            steps = [f"quotient = x^2 + ({q1})*x + ({q0})", f"remainder = {rem}"]
            answer = f"x^2 + ({q1})*x + ({q0}) with remainder {rem}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_remainder_theorem":
        if difficulty == "beginner":
            # Linear polynomial P(x)=ax+b
            c = rng.choice([1, 2, 3])
            a = rng.choice([1, 2, 3])
            b = rng.choice([-4, -2, 1, 3, 5])
            rem = a * c + b
            problem_text = f"Find the remainder when P(x)={a}*x + ({b}) is divided by x-({c})."
            steps = [f"remainder = P({c})", f"remainder = {a}*{c} + ({b})", f"remainder = {rem}"]
        elif difficulty == "intermediate":
            # Quadratic polynomial
            c = rng.choice([1, 2, 3, 4])
            a = rng.choice([1, 2, 3])
            b = rng.choice([-4, -2, 1, 3, 5])
            d = rng.choice([-6, -2, 1, 4, 7])
            rem = a * (c**2) + b * c + d
            problem_text = f"Find the remainder when P(x)={a}*x^2 + ({b})*x + ({d}) is divided by x-({c})."
            steps = [f"remainder = P({c})", f"remainder = {a}*{c}^2 + ({b})*{c} + ({d})", f"remainder = {rem}"]
        else:  # advanced — cubic
            c = rng.choice([1, 2, 3])
            a3 = rng.choice([1, 2])
            a2 = rng.choice([-3, -1, 0, 2, 3])
            a1 = rng.choice([-4, -2, 1, 3])
            a0 = rng.choice([-6, -2, 1, 4])
            rem = a3*(c**3) + a2*(c**2) + a1*c + a0
            problem_text = f"Find the remainder when P(x)={a3}*x^3 + ({a2})*x^2 + ({a1})*x + ({a0}) is divided by x-({c})."
            steps = [
                f"remainder = P({c})",
                f"remainder = {a3}*{c}^3 + ({a2})*{c}^2 + ({a1})*{c} + ({a0})",
                f"remainder = {rem}",
            ]
        answer = str(rem)
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_factor_theorem":
        if difficulty == "beginner":
            c = rng.choice([1, -1, 2])
        elif difficulty == "intermediate":
            c = rng.choice([1, 2, 3, 4, -1, -2])
        else:  # advanced — find which of several values is a zero
            c = rng.choice([1, 2, 3, -1, -2, -3])
            wrong = rng.choice([v for v in [1, 2, 3, -1, -2, -3] if v != c])
            a1 = -(c + wrong)
            a0 = c * wrong
            problem_text = f"Given P(x)=x^2+({a1})*x+({a0}), verify x={c} is a zero, then state a factor."
            steps = [
                f"P({c}) = {c}^2+({a1})*{c}+({a0}) = 0",
                f"x = {c} is a zero",
                f"factor = x-({c})",
            ]
            answer = f"x-({c})"
            return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)
        problem_text = f"If P({c}) = 0, what factor must P(x) have?"
        steps = [f"P({c}) = 0 means x = {c} is a zero", f"factor = x-({c})"]
        answer = f"x-({c})"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_zeros_polynomials":
        if difficulty == "beginner":
            roots = rng.sample([1, 2, 3, 4], 2)
            problem_text = f"Find all zeros of (x-({roots[0]}))*(x-({roots[1]})). "
            steps = [f"x = {roots[0]} or x = {roots[1]}"]
            answer = f"x={roots[0]} or x={roots[1]}"
        elif difficulty == "intermediate":
            roots = rng.sample([1, 2, 3, 4, -1, -2, -3], 3)
            problem_text = f"Find all zeros of (x-({roots[0]}))*(x-({roots[1]}))*(x-({roots[2]})). "
            steps = [f"x = {roots[0]}, x = {roots[1]}, or x = {roots[2]}"]
            answer = f"x={roots[0]}, x={roots[1]}, x={roots[2]}"
        else:  # advanced — multiplicity
            r = rng.choice([1, 2, 3])
            other = rng.choice([v for v in [1, 2, 3, 4, -1, -2] if v != r])
            problem_text = f"Find all zeros (with multiplicity) of (x-({r}))^2*(x-({other}))."
            steps = [
                f"x = {r} (multiplicity 2), x = {other} (multiplicity 1)",
            ]
            answer = f"x={r} (mult 2), x={other} (mult 1)"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_rational_functions":
        b = rng.choice([-5, -3, -2, 1, 3])
        c = rng.choice([-4, -1, 2, 5])
        while c == -b:
            c = rng.choice([-4, -1, 2, 5])
        if difficulty == "beginner":
            # Equal degree numerator/denominator → HA y=1
            problem_text = f"For f(x)=(x+({b}))/(x-({c})), find domain and asymptotes."
            steps = [f"domain: x != {c}", f"vertical asymptote: x = {c}", "horizontal asymptote: y = 1"]
            answer = f"domain x!={c}, VA x={c}, HA y=1"
        elif difficulty == "intermediate":
            # Degree numerator < denominator → HA y=0
            a = rng.choice([1, 2, 3])
            problem_text = f"For f(x)={a}/(x-({c})), find domain and asymptotes."
            steps = [f"domain: x != {c}", f"vertical asymptote: x = {c}", "horizontal asymptote: y = 0"]
            answer = f"domain x!={c}, VA x={c}, HA y=0"
        else:  # advanced — two vertical asymptotes
            c2 = rng.choice([v for v in [-3, -2, 3, 4] if v != c])
            problem_text = f"For f(x)=(x+({b}))/((x-({c}))*(x-({c2}))), find domain and asymptotes."
            steps = [
                f"domain: x != {c} and x != {c2}",
                f"vertical asymptotes: x = {c} and x = {c2}",
                "horizontal asymptote: y = 0",
            ]
            answer = f"VA x={c} and x={c2}, HA y=0"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_polynomial_inequalities":
        if difficulty == "beginner":
            # Two positive roots, > 0
            r1, r2 = sorted(rng.sample([1, 2, 3, 4, 5], 2))
            problem_text = f"Solve (x-{r1})*(x-{r2}) > 0."
            steps = [f"zeros at x = {r1} and x = {r2}", f"solution: x < {r1} or x > {r2}"]
            answer = f"x<{r1} or x>{r2}"
        elif difficulty == "intermediate":
            # Mixed-sign roots, choice of > or <
            r1, r2 = sorted(rng.sample([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5], 2))
            if rng.choice([True, False]):
                problem_text = f"Solve (x-({r1}))*(x-({r2})) > 0."
                steps = [f"zeros at x = {r1} and x = {r2}", f"solution: x < {r1} or x > {r2}"]
                answer = f"x<{r1} or x>{r2}"
            else:
                problem_text = f"Solve (x-({r1}))*(x-({r2})) < 0."
                steps = [f"zeros at x = {r1} and x = {r2}", f"solution: {r1} < x < {r2}"]
                answer = f"{r1}<x<{r2}"
        else:  # advanced — three roots
            rs = sorted(rng.sample([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5], 3))
            r1, r2, r3 = rs
            problem_text = f"Solve (x-({r1}))*(x-({r2}))*(x-({r3})) >= 0."
            steps = [
                f"zeros at x = {r1}, x = {r2}, x = {r3}",
                f"solution: {r1} <= x <= {r2} or x >= {r3}",
            ]
            answer = f"{r1}<=x<={r2} or x>={r3}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_rational_inequalities":
        zero = rng.choice([-4, -2, -1, 1, 2, 4])
        pole = rng.choice([-5, -3, 3, 5])
        while pole == zero:
            pole = rng.choice([-5, -3, 3, 5])
        low, high = sorted([pole, zero])
        if difficulty == "beginner":
            # Only positive zero/pole, simple >= 0
            zero = rng.choice([1, 2, 3])
            pole = rng.choice([4, 5, 6])
            low, high = zero, pole
            problem_text = f"Solve (x-{zero})/(x-{pole}) >= 0."
            steps = [f"critical points: x = {zero}, x = {pole}", f"solution: x <= {low} or x > {high}"]
            answer = f"x<={low} or x>{high}"
        elif difficulty == "intermediate":
            problem_text = f"Solve (x-({zero}))/(x-({pole})) >= 0."
            steps = [f"critical points: x = {zero}, x = {pole}", f"solution: x < {low} or x >= {high}"]
            answer = f"x<{low} or x>={high}"
        else:  # advanced — strict inequality with sign chart
            problem_text = f"Solve (x-({zero}))/(x-({pole})) < 0."
            steps = [
                f"critical points: x = {zero}, x = {pole}",
                f"sign chart: negative between {low} and {high}",
                f"solution: {low} < x < {high}",
            ]
            answer = f"{low}<x<{high}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "precalculus_graph_transformations":
        h = rng.choice([1, 2, 3, 4])
        k = rng.choice([-3, -1, 1, 2, 4])
        a = rng.choice([2, 3, -1, -2])
        if difficulty == "beginner":
            # Shift only (a=1), sqrt parent
            problem_text = f"Describe g(x)=sqrt(x-{h})+({k}) relative to f(x)=sqrt(x)."
            steps = [f"shift right {h}", f"shift up {k}"]
            answer = f"right {h}, up {k}"
        elif difficulty == "intermediate":
            # Scale + shift, sqrt parent
            problem_text = f"Describe g(x)={a}*sqrt(x-{h})+({k}) relative to f(x)=sqrt(x)."
            steps = [f"vertical scale/reflection by {a}", f"shift right {h}", f"shift up {k}"]
            answer = f"scale {a}, right {h}, up {k}"
        else:  # advanced — absolute value parent with full transformations
            problem_text = f"Describe g(x)={a}*|x-{h}|+({k}) relative to f(x)=|x|."
            steps = [f"vertical scale/reflection by {a}", f"shift right {h}", f"shift up {k}"]
            answer = f"scale {a}, right {h}, up {k}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "precalculus_piecewise_analysis":
        a = rng.choice([1, 2, 3, 4])
        neg_x = rng.choice([-4, -3, -2, -1])
        pos_x = rng.choice([0, 1, 2, 3, 4])
        if difficulty == "beginner":
            # Both pieces use simple linear rules
            m1 = rng.choice([1, 2])
            m2 = rng.choice([1, 2, 3])
            problem_text = f"For f(x)={m1}*x if x<0 and f(x)={m2}*x if x>=0, find f({neg_x}) and f({pos_x})."
            steps = [f"f({neg_x}) = {m1}*({neg_x}) = {m1*neg_x}", f"f({pos_x}) = {m2}*{pos_x} = {m2*pos_x}"]
            answer = f"f({neg_x})={m1*neg_x}, f({pos_x})={m2*pos_x}"
        elif difficulty == "intermediate":
            # Quadratic + linear
            problem_text = f"For f(x)=x^2 if x<0 and f(x)={a}*x if x>=0, find f({neg_x}) and f({pos_x})."
            steps = [f"f({neg_x}) = ({neg_x})^2 = {neg_x*neg_x}", f"f({pos_x}) = {a}*{pos_x} = {a*pos_x}"]
            answer = f"f({neg_x})={neg_x*neg_x}, f({pos_x})={a*pos_x}"
        else:  # advanced — 3-piece function
            x_mid = rng.choice([0, 1, 2])
            x_hi = x_mid + rng.choice([2, 3, 4])
            x_lo = rng.choice([-4, -3, -2])
            problem_text = (
                f"For f(x)=x^2 if x<{x_mid}, f(x)={a} if {x_mid}<=x<{x_hi}, f(x)={a}*x if x>={x_hi}, "
                f"find f({x_lo}), f({x_mid}), f({x_hi})."
            )
            steps = [
                f"f({x_lo}) = ({x_lo})^2 = {x_lo*x_lo}",
                f"f({x_mid}) = {a}",
                f"f({x_hi}) = {a}*{x_hi} = {a*x_hi}",
            ]
            answer = f"f({x_lo})={x_lo*x_lo}, f({x_mid})={a}, f({x_hi})={a*x_hi}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "precalculus_log_properties":
        base = rng.choice([2, 3, 5, 10])
        power = rng.choice([1, 2, 3, 4])
        coeff = base ** power
        if difficulty == "beginner":
            # Product rule expand
            problem_text = f"Expand log base {base} of ({coeff}*x)."
            steps = [
                f"log_{base}({coeff}*x) = log_{base}({coeff}) + log_{base}(x)",
                f"log_{base}({coeff}*x) = {power} + log_{base}(x)",
            ]
            answer = f"{power} + log_{base}(x)"
        elif difficulty == "intermediate":
            # Quotient rule
            problem_text = f"Expand log base {base} of ({coeff}/x)."
            steps = [
                f"log_{base}({coeff}/x) = log_{base}({coeff}) - log_{base}(x)",
                f"log_{base}({coeff}/x) = {power} - log_{base}(x)",
            ]
            answer = f"{power} - log_{base}(x)"
        else:  # advanced — power rule + product
            p2 = rng.choice([2, 3])
            problem_text = f"Expand log base {base} of ({coeff}*x^{p2})."
            steps = [
                f"log_{base}({coeff}*x^{p2}) = log_{base}({coeff}) + log_{base}(x^{p2})",
                f"= {power} + {p2}*log_{base}(x)",
            ]
            answer = f"{power} + {p2}*log_{base}(x)"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_inverse_functions":
        if difficulty == "beginner":
            # a=1, simple y=x+b
            b = rng.choice([-4, -2, 0, 2, 3, 5])
            problem_text = f"Find inverse of f(x)=x+({b})."
            steps = [f"y = x+({b})", f"x = y+({b})", f"y = x-({b})"]
            answer = f"x-({b})"
        elif difficulty == "intermediate":
            a = rng.choice([2, 3, 4, 5])
            b = rng.choice([-6, -4, -2, 1, 3, 5])
            problem_text = f"Find inverse of f(x)={a}*x+({b})."
            steps = [f"y = {a}*x+({b})", f"x = {a}*y+({b})", f"y = (x-({b}))/{a}"]
            answer = f"(x-({b}))/{a}"
        else:  # advanced — verify inverse by composition
            a = rng.choice([2, 3, 4, 5])
            b = rng.choice([-6, -4, -2, 1, 3, 5])
            problem_text = f"Find inverse of f(x)={a}*x+({b}) and verify f(f^-1(x))=x."
            steps = [
                f"y = {a}*x+({b})",
                f"x = {a}*y+({b})",
                f"f^-1(x) = (x-({b}))/{a}",
                f"f(f^-1(x)) = {a}*((x-({b}))/{a})+({b}) = x",
            ]
            answer = f"(x-({b}))/{a}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "precalculus_exponential_functions":
        if difficulty == "beginner":
            # Evaluate: no solving, just compute
            b = rng.choice([2, 3])
            x_val = rng.choice([1, 2, 3])
            result = b ** x_val
            problem_text = f"Evaluate {b}^{x_val}."
            steps = [f"{b}^{x_val} = {result}"]
            answer = str(result)
        elif difficulty == "intermediate":
            a = rng.choice([1, 2, 3])
            b = rng.choice([2, 3, 4])
            x_true = rng.choice([1, 2, 3])
            rhs = a * (b ** x_true)
            problem_text = f"Solve {a}*{b}^x = {rhs}."
            steps = [f"{b}^x = {rhs}/{a}", f"{b}^x = {b**x_true}", f"x = {x_true}"]
            answer = f"x={x_true}"
        else:  # advanced — growth/decay word problem
            P = rng.choice([100, 200, 500, 1000])
            r = rng.choice([1.05, 1.10, 1.15, 0.90, 0.85])
            t = rng.choice([2, 3, 4, 5])
            result = round(P * (r ** t), 2)
            direction = "growth" if r > 1 else "decay"
            problem_text = f"A population of {P} grows/decays at rate {r} per year. Find value after {t} years."
            steps = [f"A = {P}*({r})^{t}", f"A = {fmt_num(result)}"]
            answer = fmt_num(result)
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "precalculus_logarithmic_functions":
        base = rng.choice([2, 3, 4, 5, 10])
        y = rng.choice([1, 2, 3, 4])
        x_val = base ** y
        if difficulty == "beginner":
            # base 2 or 10 only, y=1,2
            base = rng.choice([2, 10])
            y = rng.choice([1, 2])
            x_val = base ** y
            problem_text = f"Evaluate log base {base} of {x_val}."
            steps = [f"{base}^x = {x_val}", f"x = {y}"]
            answer = str(y)
        elif difficulty == "intermediate":
            problem_text = f"Evaluate log base {base} of {x_val}."
            steps = [f"{base}^x = {x_val}", f"x = {y}"]
            answer = str(y)
        else:  # advanced — solve log equation
            c = rng.choice([1, 2, 3])
            rhs = base ** (y + c)
            problem_text = f"Solve log base {base} of (x+{c}) = {y}."
            steps = [
                f"x+{c} = {base}^{y}",
                f"x+{c} = {x_val}",
                f"x = {x_val - c}",
            ]
            answer = f"x={x_val - c}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    # Build per-concept templates.
    if concept == "algebra_linear_equations":
        if difficulty == "beginner":
            a = rng.choice([1, 2, 3, 4, 5])
            x = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            b = rng.choice([-10, -5, -3, 2, 5, 7, 9, 10])
        else:
            a = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
            x = rng.choice([-10, -9, -8, -6, -4, -2, 2, 3, 5, 7, 8, 9])
            b = rng.choice([-20, -15, -10, -7, 7, 10, 15, 20])
        c = a * x + b
        problem_text = f"Solve for x: {a}x + ({b}) = {c}"
        steps = [f"{a}*x = {c - b}", f"x = {x}"]
        answer = f"x={x}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_quadratic_equations":
        if difficulty == "beginner":
            r1, r2 = rng.sample([1, 2, 3, 4, 5], 2)
        elif difficulty == "intermediate":
            roots = [-5, -4, -3, -2, 2, 3, 4, 5]
            r1, r2 = rng.sample(roots, 2)
        else:
            roots = [-8, -6, -5, -4, -3, 2, 3, 4, 6, 8]
            r1, r2 = rng.sample(roots, 2)
        r_low, r_high = sorted([r1, r2])
        b = -(r_low + r_high)
        c = r_low * r_high
        problem_text = f"Solve for x: x^2 + ({b})x + ({c}) = 0"
        steps = [
            f"x^2 + ({b})*x + ({c}) = (x-({r_low}))*(x-({r_high}))",
            f"(x-({r_low}))*(x-({r_high})) = 0",
            f"x = {r_low}",
            f"x = {r_high}",
        ]
        answer = f"x={r_low} or x={r_high}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_systems_equations":
        # Use the structured system: x + y = s, x - y = t
        if difficulty == "beginner":
            x = rng.choice([2, 3, 4, 5, 6])
            y = rng.choice([1, 2, 3, 4, 5])
        else:
            x = rng.choice([-6, -4, -3, -2, 2, 3, 4, 6])
            y = rng.choice([-5, -4, -3, -2, 2, 3, 5])
        s = x + y
        t = x - y
        problem_text = f"Solve the system: x + y = {s} and x - y = {t}"
        steps = [f"2*x = {s + t}", f"x = {x}", f"y = {y}"]
        answer = f"x={x}, y={y}"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "algebra_factoring":
        if difficulty == "beginner":
            r1, r2 = rng.sample([1, 2, 3, 4, 5], 2)
        elif difficulty == "intermediate":
            roots = [-5, -4, -3, 2, 3, 4, 5]
            r1, r2 = rng.sample(roots, 2)
        else:
            roots = [-8, -6, -5, -4, -3, 2, 3, 4, 6, 8]
            r1, r2 = rng.sample(roots, 2)
        r_low, r_high = sorted([r1, r2])
        b = -(r_low + r_high)
        c = r_low * r_high
        problem_text = f"Factor: x^2 + ({b})x + ({c})"
        steps = [
            f"x^2 + ({b})*x + ({c}) = (x-({r_low}))*(x-({r_high}))",
            f"(x-({r_low}))*(x-({r_high}))",
        ]
        answer = f"(x-({r_low}))*(x-({r_high}))"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "calculus_limits":
        a = rng.choice([1, 2, 3, 4, 5])
        problem_text = f"Evaluate: lim_{{x-> {a}}} (x^2)"
        steps = [f"({a})^2", f"{a*a}"]
        answer = str(a * a)
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "calculus_derivatives":
        if difficulty == "beginner":
            n = rng.choice([2, 3, 4, 5])
        else:
            n = rng.choice([2, 3, 4, 5, 6, 7, 8])
        problem_text = f"Find the derivative of f(x)=x^{n}"
        steps = [f"{n}*x^({n-1})"]
        answer = f"{n}*x^({n-1})"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "calculus_integrals":
        if difficulty == "intermediate":
            n = rng.choice([0, 1, 2, 3, 4])
        else:
            n = rng.choice([1, 2, 3, 4, 5])
        problem_text = f"Compute: ∫ x^{n} dx"
        # Ignore +C for step-by-step parsing; user can optionally include it.
        steps = [f"x^({n+1})/({n+1})"]
        answer = f"x^({n+1})/({n+1}) + C"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "geometry_area":
        if difficulty == "beginner":
            l = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
            w = rng.choice([2, 3, 4, 5, 6, 7, 8])
        else:
            l = rng.choice([3, 4, 5, 6, 7, 8, 9, 10, 12])
            w = rng.choice([2, 3, 4, 5, 6, 8, 10])
        problem_text = f"Find area of a rectangle: length {l}, width {w}"
        steps = [f"{l}*{w}", str(l * w)]
        answer = str(l * w)
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "geometry_volume":
        l = rng.choice([1, 2, 3, 4, 5])
        w = rng.choice([2, 3, 4, 5])
        h = rng.choice([2, 3, 4, 5])
        problem_text = f"Find volume of a prism: l={l}, w={w}, h={h}"
        steps = [f"{l}*{w}*{h}", str(l * w * h)]
        answer = str(l * w * h)
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "geometry_pythagorean":
        a = rng.choice([3, 4, 5, 6, 7])
        b = rng.choice([4, 5, 6, 7, 8])
        c_sq = a * a + b * b
        c = int(c_sq ** 0.5)
        # If not perfect square, retry once to keep step verification simple.
        if c * c != c_sq:
            a, b = 3, 4
            c_sq = a * a + b * b
            c = 5
        problem_text = f"Use the Pythagorean theorem: a={a}, b={b}. Find c."
        steps = [f"{a}^2 + {b}^2", str(c)]
        answer = str(c)
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "trigonometry_basic":
        # Special angles with exact sin values.
        angles = [
            (r"pi/6", "1/2"),
            (r"pi/4", r"sqrt(2)/2"),
            (r"pi/3", r"sqrt(3)/2"),
            (r"pi/2", "1"),
        ]
        ang, val = rng.choice(angles)
        problem_text = f"Find sin({ang}) as an exact value."
        steps = [f"sin({ang})", val]
        answer = val
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "trigonometry_unit_circle":
        angles = [
            (r"pi/3", "1/2"),
            (r"pi/4", r"sqrt(2)/2"),
            (r"pi/6", r"sqrt(3)/2"),
            (r"pi/2", "0"),
        ]
        ang, val = rng.choice(angles)
        problem_text = f"Find cos({ang}) as an exact value."
        steps = [f"cos({ang})", val]
        answer = val
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    if concept == "trigonometry_identities":
        # A fixed but high-signal identity for Phase 1.
        problem_text = "Simplify: sin(x)^2 + cos(x)^2"
        steps = ["sin(x)^2 + cos(x)^2", "1"]
        answer = "1"
        return _pack_problem(concept, difficulty, problem_text, steps, answer, common_mistakes)

    # Fallback: use the first sample problem for the requested difficulty.
    sample = next((sp for sp in concept_details.get("sample_problems", []) if sp.get("difficulty") == difficulty), None)
    if sample is None and concept_details.get("sample_problems"):
        sample = concept_details["sample_problems"][0]
    if sample is None:
        raise ValueError(f"No mock template available for concept={concept}, difficulty={difficulty}")

    steps = list(sample["steps"])
    answer = str(sample["answer"])
    problem_text = sample["problem_statement"]
    return _pack_problem(concept, difficulty, problem_text, steps, answer, sample.get("common_mistakes", common_mistakes))


def _pack_problem(concept: str, difficulty: str, problem_text: str, steps: list[str], answer: str, common_mistakes: list[str]) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "concept_id": concept,
        "difficulty": difficulty,
        "problem": problem_text,
        "steps": steps,
        "answer": answer,
        "common_mistakes": list(common_mistakes),
        "generated_at": datetime.utcnow().isoformat(),
        "source": "mock",
    }


def get_solution_steps(problem: dict[str, Any]) -> list[str]:
    return list(problem.get("steps", []))


def verify_solution(problem: dict[str, Any], user_steps: list[str]) -> bool:
    """
    Verify a full attempt.
    For Phase 1 we check equivalence for each entered step against the internal solution,
    and also confirm the final answer matches.
    """
    correct_steps = get_solution_steps(problem)
    if len(user_steps) != len(correct_steps):
        return False

    for user_step, correct_step in zip(user_steps, correct_steps):
        if not check_answer_equivalence(user_step, correct_step):
            return False

    # Final answer check against the provided answer string.
    if user_steps:
        # Some tutors allow the final numeric value at the last step; verify it too.
        if not check_answer_equivalence(user_steps[-1], str(problem.get("answer", ""))):
            return False
    return True


def check_answer_equivalence(user_answer: str, correct_answer: str) -> bool:
    """
    SymPy-first equivalence check, with targeted parsing for common "x=... or x=..." outputs.
    """
    user_answer = str(user_answer).strip()
    correct_answer = str(correct_answer).strip()

    # Root set outputs (quadratic/factoring): compare extracted number sets.
    if (" or " in correct_answer.lower()) or ("x=" in correct_answer.lower() and "," in correct_answer) or (" or " in user_answer.lower()):
        user_nums = _extract_number_set(user_answer)
        correct_nums = _extract_number_set(correct_answer)
        return bool(correct_nums) and correct_nums.issubset(user_nums) and user_nums.issubset(correct_nums)

    # Systems outputs: compare x=... and y=...
    if "x=" in correct_answer.lower() and "y=" in correct_answer.lower():
        ux, uy = _extract_xy_pair(user_answer)
        cx, cy = _extract_xy_pair(correct_answer)
        return ux is not None and uy is not None and cx is not None and cy is not None and abs(ux - cx) < 1e-9 and abs(uy - cy) < 1e-9

    # Fallback to SymPy expression equivalence.
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import (
            convert_xor,
            implicit_multiplication_application,
            parse_expr,
            standard_transformations,
        )

        transform = standard_transformations + (implicit_multiplication_application, convert_xor)

        def parse_expr_only(s: str) -> sp.Expr:
            s = _normalize_math_string(s)
            # Drop constant of integration from answers (C or + C)
            s = re.sub(r"\b\+?\s*C\b", "", s, flags=re.IGNORECASE).strip()
            s = s.replace("π", "pi")
            return parse_expr(s, transformations=transform, evaluate=True)

        def parse_equation(s: str) -> tuple[sp.Expr, sp.Expr] | None:
            if "=" not in s:
                return None
            parts = s.split("=", 1)
            lhs = parse_expr_only(parts[0])
            rhs = parse_expr_only(parts[1])
            return lhs, rhs

        user_has_eq = "=" in user_answer
        correct_has_eq = "=" in correct_answer

        # If both are equations, compare (lhs-rhs) expressions.
        if user_has_eq and correct_has_eq:
            parsed_u = parse_equation(user_answer)
            parsed_c = parse_equation(correct_answer)
            if parsed_u is None or parsed_c is None:
                return False
            u_lhs, u_rhs = parsed_u
            c_lhs, c_rhs = parsed_c
            du = sp.simplify(u_lhs - u_rhs)
            dc = sp.simplify(c_lhs - c_rhs)
            return sp.simplify(du - dc) == 0

        # If neither has an equality, compare as expressions.
        if (not user_has_eq) and (not correct_has_eq):
            u_expr = parse_expr_only(user_answer)
            c_expr = parse_expr_only(correct_answer)
            if (u_expr.is_Number or c_expr.is_Number) and u_expr == c_expr:
                return True
            return sp.simplify(u_expr - c_expr) == 0

        # Mixed cases: fall back to a forgiving parse by comparing numeric values
        # when possible (so expressions like 4 are accepted for a simplified RHS).
        if user_has_eq and (not correct_has_eq):
            # user has equality, take RHS only
            rhs = user_answer.split("=", 1)[1].strip()
            return check_answer_equivalence(rhs, correct_answer)
        if (not user_has_eq) and correct_has_eq:
            rhs = correct_answer.split("=", 1)[1].strip()
            return check_answer_equivalence(user_answer, rhs)

        return False
    except Exception:
        # Last resort: normalized string equality.
        return _normalize_math_string(user_answer).replace(" ", "") == _normalize_math_string(correct_answer).replace(" ", "")


