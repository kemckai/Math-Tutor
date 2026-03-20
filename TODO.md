# Math Tutor App — TODO

Items are grouped by area. Prefix key: `[bug]` = broken behavior, `[feature]` = new capability, `[cleanup]` = tech debt / stale code.

---

## Validation

- [ ] `[feature]` **Textual "is a function" / "is not a function" validator** — currently relies on a normalized string heuristic. Add a dedicated rule that checks for the specific phrasing more robustly (e.g. "function", "is a function", "not a function", "passes vertical line test").
- [ ] `[feature]` **Validator: interval notation** — steps written as `(-∞, 3)` or `[1, 5)` are not handled by SymPy; add a normalization + comparison path for interval answers.
- [ ] `[feature]` **Validator: set notation** — answers like `{x | x ≠ 2}` or `ℝ \ {2}` need a dedicated parse path.
- [ ] `[feature]` **Validator: matrix / augmented matrix steps** — no support yet; would be needed if systems-of-equations is extended to Gaussian elimination.

---

## Problem Generators

- [ ] `[feature]` **Difficulty scaling for legacy trig generators** — `trigonometry_basic`, `trigonometry_unit_circle`, and `trigonometry_identities` use a fixed problem or a flat pool; add `intermediate` / `advanced` branches (e.g., reference angles in other quadrants, inverse trig, compound identities).
- [ ] `[feature]` **Difficulty scaling for legacy calculus generators** — `calculus_limits`, `calculus_derivatives`, `calculus_integrals` only branch on one or two levels; add more parameter variety and problem types (chain rule, u-substitution) at `advanced`.
- [ ] `[feature]` **Difficulty scaling for geometry** — `geometry_volume` and `geometry_pythagorean` ignore `difficulty`; add harder shapes (cones, spheres) and Pythagorean triples with decimal legs at `advanced`.
- [ ] `[cleanup]` **Degree symbol support in generator** — `_normalize_math_string` strips `°` with a comment "degrees not supported in Phase 1". Implement degree normalization (convert `30°` → `pi/6` or keep as numeric) so trig problems can use degree notation.
- [ ] `[feature]` **More rational-functions variants** — advanced branch currently always produces HA y=0 when degree(num) < degree(denom); add oblique/slant asymptote problems.
- [ ] `[feature]` **Word-problem variants for algebra** — most generators produce symbolic problems; add optional word-problem framing for `applied_*` and `algebra_linear_*` concepts at `intermediate`/`advanced`.

---

## OCR & Canvas

- [ ] `[feature]` **Fraction / division bar OCR** — hand-drawn fractions (`—`) are frequently confused with minus signs. Add post-process heuristic: if a `—` appears between two numeric expressions it is likely a division bar.
- [ ] `[feature]` **Superscript exponent OCR** — exponents written small and above a base are often dropped or misread (e.g., `x²` → `x2`). Add a normalization step that converts inline superscript patterns to `^`.
- [ ] `[feature]` **Greek letter OCR** — `π`, `θ`, `α` come back as garbage characters from some OCR engines. Extend `ocr_processor.py` normalization table for common Greek letters.
- [ ] `[feature]` **Canvas multi-stroke undo** — currently only the eraser corrects mistakes; add a keyboard shortcut or button for single-stroke undo (Ctrl+Z).

---

## Mastery & Progress

- [ ] `[feature]` **Spaced repetition schedule** — mastery level is currently raw `problems_correct / problems_attempted`. Implement a simple SM-2-style decay so concepts drift back toward "needs practice" over time.
- [ ] `[feature]` **Difficulty-weighted mastery** — a correct answer at `advanced` should increase mastery more than one at `beginner`. Add a weight multiplier to `upsert_progress`.
- [ ] `[feature]` **Prerequisite unlock in UI** — `concepts/prerequisites.py` has a working `get_recommended_next` function, but the concept selector in `app.py` always shows all 40 concepts. Wire prerequisites so locked concepts are greyed out or hidden until their prerequisites reach a mastery threshold.
- [ ] `[feature]` **"Next recommended concept" suggestion** — after completing a problem, call `get_recommended_next` and surface the top suggestion to the user.
- [ ] `[feature]` **Problem history review** — `db_manager.record_attempt` exists but is not called anywhere in `app.py`. Call it on problem completion, then add a "History" sidebar tab showing past attempts per concept.
- [ ] `[feature]` **Session timer display** — `session_start_ts` is set in `SessionState` but never shown. Display elapsed session time in the sidebar.

---

## Code Quality / Tech Debt

- [ ] `[cleanup]` **Stale `username` field in `SessionState`** — `session_manager.py` still has `username: str` in the dataclass and hardcodes `user_id=1`. The whole module is a placeholder; either implement it properly (read from session state) or remove the unused dataclass.
- [ ] `[cleanup]` **`get_session_state()` is a stub** — the function returns a hardcoded `user_id=1`; it is never called from `app.py`, which manages user_id directly. Either wire it up or delete it.
- [ ] `[cleanup]` **`db_manager.py` section comments say "placeholders"** — the `# --- Concept progress (placeholders) ---` and `# --- Problem history (placeholders) ---` comments are stale now that the methods are implemented; update to accurate headings.
- [ ] `[cleanup]` **Remove "Phase 1" labels from docstrings** — `hint_system.py`, `ocr_processor.py`, `canvas_handler.py`, `step_validator.py`, and `problem_generator.py` all reference "Phase 1" in module docstrings. Replace with accurate descriptions.
- [ ] `[cleanup]` **`trigonometry_identities` fixed problem** — generator always returns `sin(x)^2 + cos(x)^2 = 1` with a hard-coded comment "A fixed but high-signal identity for Phase 1". Replace with a pool of identities so repeated practice remains useful.

---

## UI / UX

- [ ] `[feature]` **Problem re-attempt** — after getting a problem wrong there is no way to retry it. Add a "Try again" button that reuses the same problem.
- [ ] `[feature]` **Show step count progress** — when a problem has multiple steps (e.g. 4 steps), show `Step 2 / 4` so the student understands how far through the solution they are.
- [ ] `[feature]` **Persist in-progress steps** — if the user switches concept mid-problem, their canvas and typed steps are lost. Store in-progress state in session or warn before navigating away.
- [ ] `[feature]` **Dark/light mode toggle** — the CSS theme is hard-coded to black background; adding a light-mode toggle would improve accessibility.
- [ ] `[feature]` **Keyboard shortcut for "Check step"** — students working at a keyboard should be able to hit Enter to submit a step without clicking the button.
