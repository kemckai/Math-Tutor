import time
import re

import streamlit as st
try:
    import altair as alt
except ImportError:
    alt = None  # type: ignore[assignment]

from config import get_settings
from concepts.concept_library import get_all_concepts, get_concept_details, get_next_concepts
from database.db_manager import AttemptRecord, DatabaseManager
from database.models import Concept
from recognition.canvas_handler import get_latest_canvas_ocr, render_canvas
from tutor.problem_generator import generate_problem
from tutor.step_validator import get_progress_percentage, validate_step
from logger import get_logger

logger = get_logger()


def _concept_options() -> list[tuple[str, str]]:
    concepts = get_all_concepts()
    # Sort by category, then name.
    return sorted(
        [(cid, f"{details['category']} - {details['name']}") for cid, details in concepts.items()],
        key=lambda t: t[1].lower(),
    )


def _ensure_concepts_in_db(db: DatabaseManager) -> None:
    concepts = get_all_concepts()
    to_upsert: list[tuple[str, Concept]] = []
    for cid, details in concepts.items():
        to_upsert.append(
            (
                cid,
                Concept(id=cid, name=str(details["name"]), category=str(details["category"]), description=str(details["description"])),
            )
        )
    db.upsert_concepts(to_upsert)


def _compute_completed_concepts(progress_rows: list[dict]) -> list[str]:
    # Lightweight heuristic: "completed" when mastery is high enough.
    completed: list[str] = []
    for row in progress_rows:
        if row.get("problems_attempted", 0) and row.get("mastery_level", 0.0) >= 70.0:
            completed.append(row["concept_id"])
    return completed


def _apply_red_black_yellow_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --mt-black: #0B0B0B;
            --mt-black-soft: #171717;
            --mt-red: #C1121F;
            --mt-red-soft: #8D0E17;
            --mt-yellow: #FFD000;
            --mt-yellow-soft: #E5B700;
            --mt-text: #FFE88A;
        }

        .stApp {
            background-color: var(--mt-black);
            color: var(--mt-text);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--mt-red-soft) 0%, var(--mt-red) 100%);
            border-right: 2px solid var(--mt-yellow);
        }

        [data-testid="stSidebar"] * {
            color: #FFF3BF !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--mt-yellow) !important;
        }

        p, span, label, li, div {
            color: var(--mt-text);
        }

        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea {
            background-color: var(--mt-black-soft) !important;
            color: var(--mt-yellow) !important;
            border: 1px solid var(--mt-yellow) !important;
        }

        .stButton > button {
            background-color: var(--mt-yellow) !important;
            color: var(--mt-black) !important;
            border: 1px solid var(--mt-yellow-soft) !important;
            font-weight: 800 !important;
            text-shadow: none !important;
        }

        .stButton > button * {
            color: var(--mt-black) !important;
        }

        .stButton > button:hover {
            background-color: #FFDC3A !important;
            border-color: #FFDC3A !important;
            color: var(--mt-black) !important;
        }

        .stButton > button:focus,
        .stButton > button:active {
            color: var(--mt-black) !important;
        }

        [data-baseweb="select"] > div,
        [data-baseweb="popover"] {
            background-color: var(--mt-black-soft) !important;
            color: var(--mt-yellow) !important;
        }

        .stAlert {
            background-color: #210E0E !important;
            border: 1px solid var(--mt-red) !important;
            color: #FFE5E5 !important;
        }

        [data-testid="stMetricValue"] {
            color: var(--mt-yellow) !important;
        }

        [data-testid="stProgressBar"] div {
            background-color: var(--mt-yellow) !important;
        }

        .stExpander {
            background-color: #131313 !important;
            border: 1px solid #4B1A1A !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    settings = get_settings()
    st.set_page_config(page_title=settings.app_name, layout="wide")
    _apply_red_black_yellow_theme()

    st.title(settings.app_name)
    st.caption("Step-by-step practice with real-time step checking (SymPy-first).")

    db = DatabaseManager()
    st.session_state.setdefault("concepts_seeded", False)
    if not st.session_state.concepts_seeded:
        _ensure_concepts_in_db(db)
        st.session_state.concepts_seeded = True

    concepts = get_all_concepts()
    concept_ids = sorted(concepts.keys())
    concept_options = _concept_options()
    if not concept_ids or not concept_options:
        st.error("No concepts are available. Add at least one concept to continue.")
        return
    try:
        import pandas as pd  # type: ignore
    except Exception:
        pd = None

    # --- Sidebar: user + concept selection ---
    st.sidebar.header("Practice")

    user_id = db.get_or_create_user(settings.default_user)

    category_to_concept = {cid: details["category"] for cid, details in concepts.items()}

    selected_label = st.sidebar.selectbox("Concept", [label for _cid, label in concept_options], index=0)
    selected_concept_id = next((cid for cid, label in concept_options if label == selected_label), concept_ids[0])

    concept_details = get_concept_details(selected_concept_id)
    available_difficulties = concept_details.get("available_difficulties", ["beginner"])
    difficulty = st.sidebar.selectbox("Difficulty", available_difficulties, index=0)

    # --- Progress ---
    progress_rows = db.get_all_user_progress(user_id)
    selected_progress = db.get_user_progress(user_id, selected_concept_id)

    st.sidebar.subheader("Mastery")
    st.sidebar.metric("Mastery level", f"{selected_progress.get('mastery_level', 0.0):.0f}%")
    st.sidebar.progress(float(selected_progress.get("mastery_level", 0.0)) / 100.0)

    completed_concepts = _compute_completed_concepts(progress_rows)
    recommended = get_next_concepts(completed_concepts)

    st.sidebar.subheader("Recommended next")
    if recommended:
        for cid in recommended:
            details = get_concept_details(cid)
            st.sidebar.write(f"- {details['name']}")
    else:
        st.sidebar.write("Keep practicing—try a different concept.")

    st.sidebar.subheader("Custom Problem")
    custom_problem_input = st.sidebar.text_area(
        "Paste your own problem",
        value=st.session_state.get("custom_problem_text", ""),
        height=120,
        key="custom_problem_input",
        placeholder="e.g., Solve |x-0| = 3",
    )
    custom_expected_answer_input = st.sidebar.text_input(
        "Expected final answer (optional)",
        value=st.session_state.get("custom_expected_answer", ""),
        key="custom_expected_answer_input",
        placeholder="e.g., x=3 or x=-3",
    )
    custom_steps_input = st.sidebar.text_area(
        "Expected steps (optional, one per line)",
        value=st.session_state.get("custom_steps_raw", ""),
        height=100,
        key="custom_steps_input",
        placeholder="x-0=3 or x-0=-3\nx=3 or x=-3",
    )
    custom_col1, custom_col2 = st.sidebar.columns([1, 1])
    with custom_col1:
        use_custom_problem = st.button("Use Custom", key="use_custom_problem_btn")
    with custom_col2:
        use_generated_problem = st.button("Use Generated", key="use_generated_problem_btn")

    # Overall mastery bar chart.
    st.sidebar.subheader("All Concepts")
    chart_rows = []
    progress_map = {r["concept_id"]: r for r in progress_rows}
    for cid in concept_ids:
        row = progress_map.get(cid)
        mastery = float(row["mastery_level"]) if row else 0.0
        chart_rows.append({"concept": cid, "mastery": mastery, "category": category_to_concept[cid]})
    if pd is not None and alt is not None:
        chart_df = pd.DataFrame(chart_rows)
        _chart = (
            alt.Chart(chart_df)
            .mark_bar(color="#FFD000", opacity=0.85)
            .encode(
                x=alt.X("concept:N", sort=None, axis=alt.Axis(labelAngle=-45, labelColor="#FFF3BF", titleColor="#FFF3BF", tickColor="#FFF3BF")),
                y=alt.Y("mastery:Q", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(labelColor="#FFF3BF", titleColor="#FFF3BF", gridColor="rgba(255,255,255,0.1)")),
                tooltip=["concept", "mastery"],
            )
            .properties(height=220)
            .configure(background="transparent")
            .configure_view(strokeWidth=0)
        )
        st.sidebar.altair_chart(_chart, use_container_width=True)
    elif pd is not None:
        chart_df = pd.DataFrame(chart_rows)
        st.sidebar.bar_chart(chart_df.set_index("concept")["mastery"])
    else:
        # Fallback display without pandas.
        st.sidebar.write("Mastery overview:")
        for row in chart_rows:
            st.sidebar.write(f"- {row['concept']}: {row['mastery']:.0f}%")

    # --- Session state for the tutor loop ---
    st.session_state.setdefault("current_concept_id", None)
    st.session_state.setdefault("current_difficulty", None)
    st.session_state.setdefault("current_problem", None)
    st.session_state.setdefault("current_step_idx", 0)
    st.session_state.setdefault("user_steps", [])
    st.session_state.setdefault("attempt_start_ts", None)
    st.session_state.setdefault("step_input_text", "")
    st.session_state.setdefault("clear_step_input", False)
    st.session_state.setdefault("pending_step_input_text", None)
    st.session_state.setdefault("last_step_validation_status", None)
    st.session_state.setdefault("last_step_validation_idx", None)
    st.session_state.setdefault("confirm_next", False)
    st.session_state.setdefault("attempt_recorded_for_problem_id", None)
    st.session_state.setdefault("auto_check_step_input", False)
    st.session_state.setdefault("canvas_status_message", None)
    st.session_state.setdefault("canvas_status_level", "info")
    st.session_state.setdefault("custom_problem_mode", False)
    st.session_state.setdefault("custom_problem_text", "")
    st.session_state.setdefault("custom_expected_answer", "")
    st.session_state.setdefault("custom_steps_raw", "")

    def _start_new_problem() -> None:
        logger.info("App: Starting new problem (concept=%s, difficulty=%s)", selected_concept_id, difficulty)
        recent_texts = db.get_recent_problem_texts(user_id, selected_concept_id, settings.max_recent_problems)
        chosen = None
        for attempt in range(8):
            p = generate_problem(selected_concept_id, difficulty)
            if p.get("problem") not in recent_texts:
                chosen = p
                logger.debug("App: Generated fresh problem on attempt %d", attempt + 1)
                break
            chosen = p
        if chosen is None:
            chosen = generate_problem(selected_concept_id, difficulty)

        problem_id = chosen.get("id", "unknown")
        logger.info("App: New problem loaded (id=%s, steps=%d)", problem_id, len(chosen.get("steps", [])))
        
        st.session_state.current_problem = chosen
        st.session_state.current_step_idx = 0
        st.session_state.user_steps = []
        st.session_state.attempt_start_ts = time.time()
        st.session_state.clear_step_input = True
        st.session_state.pending_step_input_text = None
        st.session_state.last_step_validation_status = None
        st.session_state.last_step_validation_idx = None
        st.session_state.attempt_recorded_for_problem_id = None

    def _start_custom_problem(problem_text: str, expected_answer: str, custom_steps_raw: str) -> None:
        cleaned = (problem_text or "").strip()
        if not cleaned:
            return

        parsed_steps: list[str] = []
        for line in (custom_steps_raw or "").splitlines():
            normalized = re.sub(r"^\s*\d+[\).:-]?\s*", "", line).strip()
            if normalized:
                parsed_steps.append(normalized)

        st.session_state.custom_problem_mode = True
        st.session_state.custom_problem_text = cleaned
        st.session_state.custom_expected_answer = (expected_answer or "").strip()
        st.session_state.custom_steps_raw = custom_steps_raw or ""
        st.session_state.current_problem = {
            "id": f"custom-{int(time.time())}",
            "problem": cleaned,
            "steps": parsed_steps,
            "answer": (expected_answer or "").strip(),
            "common_mistakes": [],
        }
        st.session_state.current_step_idx = 0
        st.session_state.user_steps = []
        st.session_state.attempt_start_ts = time.time()
        st.session_state.clear_step_input = True
        st.session_state.pending_step_input_text = None
        st.session_state.last_step_validation_status = None
        st.session_state.last_step_validation_idx = None
        st.session_state.attempt_recorded_for_problem_id = None
        st.session_state.confirm_next = False

    if use_custom_problem:
        if custom_problem_input.strip():
            _start_custom_problem(custom_problem_input, custom_expected_answer_input, custom_steps_input)
            st.rerun()
        else:
            st.sidebar.warning("Paste a problem first.")

    if use_generated_problem:
        st.session_state.custom_problem_mode = False
        st.session_state.custom_problem_text = ""
        st.session_state.custom_expected_answer = ""
        st.session_state.custom_steps_raw = ""
        _start_new_problem()
        st.rerun()

    concept_changed = st.session_state.current_concept_id != selected_concept_id
    difficulty_changed = st.session_state.current_difficulty != difficulty
    if (not st.session_state.custom_problem_mode) and (concept_changed or difficulty_changed or st.session_state.current_problem is None):
        st.session_state.current_concept_id = selected_concept_id
        st.session_state.current_difficulty = difficulty
        _start_new_problem()

    problem = st.session_state.current_problem or {}
    steps = list(problem.get("steps", []))
    current_step_idx = int(st.session_state.current_step_idx)
    solved = current_step_idx >= len(steps) and len(steps) > 0

    # --- How-to banner ---
    with st.expander("📖 How to use this tutor", expanded=not bool(st.session_state.user_steps) and not solved):
        st.markdown("""
**Workflow — repeat until the progress bar is full:**

| \# | What to do |
|---|---|
| 1 | Read the **Problem** on the left |
| 2 | Work a single step in your head (or on paper / the canvas) |
| 3 | **Type that one step** in the answer box (e.g. `2*x = 8` or `x = 4`) |
| 4 | Click **✔ Check step** |
| 5 | ✅ Correct → you advance to the next step automatically |
| 6 | ❌ Wrong → read the feedback & hint, then try again |

**Notation cheat-sheet:** `^` = exponent &nbsp;·&nbsp; `*` = multiply &nbsp;·&nbsp; `/` = divide &nbsp;·&nbsp; `sqrt(x)` = √x &nbsp;·&nbsp; `pi` = π

**Canvas (optional):** draw your working, click **Interpret**, then **Use recognized text** to auto-fill the answer box.
""")

    # --- Main: problem + step input ---
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Problem")
        st.write(problem.get("problem", ""))

        if st.session_state.custom_problem_mode:
            custom_steps_count = len(steps)
            custom_answer = str(problem.get("answer", "")).strip()
            if custom_steps_count > 0:
                message = f"Custom problem mode: validation active ({custom_steps_count} expected step{'s' if custom_steps_count != 1 else ''} loaded)."
            else:
                message = "Custom problem mode: record-only (no expected steps provided)."
            if custom_answer:
                message += " Expected final answer is loaded."
            st.info(message)

        st.markdown("---")
        total = max(len(steps), 1)
        shown_step = min(current_step_idx + 1, total)
        st.caption(f"Step {shown_step} of {total}")
        st.progress(get_progress_percentage(problem, completed_steps=current_step_idx) / 100.0)

        if st.session_state.user_steps:
            st.markdown("**Steps verified so far:**")
            for i, s in enumerate(st.session_state.user_steps, start=1):
                st.write(f"✅ {i}. `{s}`")

        if solved:
            st.success(f"🎉 Problem solved! Final answer: `{problem.get('answer', '')}`")

    with right:
        if not solved:
            step_num = current_step_idx + 1
            st.subheader(f"Your answer — step {step_num}")

            def _submit_step(user_step: str) -> None:
                if not steps:
                    st.session_state.user_steps.append(user_step)
                    st.session_state.clear_step_input = True
                    st.session_state.last_feedback = {
                        "correct": True,
                        "feedback": "Step recorded for your custom problem.",
                        "hint": None,
                        "reason_code": "custom_recorded",
                        "reason": "Custom problem mode stores your steps without automatic correctness checking.",
                    }
                    st.session_state.last_step_validation_status = "correct"
                    st.session_state.last_step_validation_idx = current_step_idx
                    st.rerun()

                result = validate_step(problem, current_step_idx, user_step)
                if result.get("correct"):
                    st.session_state.user_steps.append(user_step)
                    st.session_state.current_step_idx = current_step_idx + 1
                    st.session_state.clear_step_input = True
                    st.session_state.last_feedback = result
                    st.session_state.last_step_validation_status = "correct"
                    st.session_state.last_step_validation_idx = current_step_idx
                    st.rerun()

                st.session_state.last_feedback = result
                st.session_state.last_step_validation_status = "incorrect"
                st.session_state.last_step_validation_idx = current_step_idx
                st.rerun()

            # --- Canvas first so Interpret can pre-fill the text input ---
            st.caption("✍️ Optional: draw your working below, then click Interpret")
            interpret_clicked, ocr_text = render_canvas()
            if interpret_clicked:
                if ocr_text:
                    st.session_state.pending_step_input_text = ocr_text
                    st.session_state.canvas_status_message = f"Recognized: `{ocr_text}`"
                    st.session_state.canvas_status_level = "success"
                else:
                    st.session_state.canvas_status_message = "I couldn't read that drawing. Try writing larger, darker, and centered in the white box."
                    st.session_state.canvas_status_level = "warning"
                st.rerun()

            # --- pending / clear text plumbing ---
            pending_text = st.session_state.pending_step_input_text
            if pending_text is not None:
                st.session_state.step_input_text = str(pending_text)
                st.session_state.pending_step_input_text = None
            elif st.session_state.clear_step_input:
                st.session_state.step_input_text = ""
                st.session_state.clear_step_input = False

            canvas_status_message = st.session_state.get("canvas_status_message")
            if canvas_status_message:
                if st.session_state.get("canvas_status_level") == "warning":
                    st.warning(canvas_status_message)
                else:
                    st.caption(canvas_status_message)

            st.text_input(
                "Type your step here (or edit the recognized text):",
                key="step_input_text",
                placeholder="e.g., 2*x = 8  or  x = 4",
                label_visibility="visible",
            )

            auto_check = bool(st.session_state.get("auto_check_step_input"))
            check_clicked = st.button("✔ Check step", key="check_step_btn", use_container_width=True)
            if auto_check:
                st.session_state.auto_check_step_input = False

            if check_clicked or auto_check:
                user_step = str(st.session_state.step_input_text).strip()

                if not user_step:
                    ocr_candidate = get_latest_canvas_ocr(force_refresh=False)
                    if ocr_candidate:
                        user_step = str(ocr_candidate).strip()

                if not user_step:
                    st.warning("Type a step or draw on the canvas and click Interpret first.")
                    st.session_state.last_step_validation_status = None
                    st.session_state.last_step_validation_idx = current_step_idx
                else:
                    _submit_step(user_step)

            # --- Feedback ---
            last_feedback = st.session_state.get("last_feedback")
            if last_feedback:
                st.markdown("---")
                if last_feedback.get("correct"):
                    st.success(last_feedback.get("feedback", "Correct!"))
                else:
                    st.error(last_feedback.get("feedback", "Not quite — try again."))
                    reason = str(last_feedback.get("reason") or "").strip()
                    if reason:
                        st.caption(f"Why: {reason}")
                    if last_feedback.get("hint"):
                        with st.expander("💡 Hint"):
                            st.write(last_feedback.get("hint"))
        else:
            st.subheader("All steps complete!")
            st.info("🎉 Well done! Click **Next problem** on the left to continue.")

    # --- Next problem flow ---
    st.divider()
    if st.button("Next Problem", key="next_problem_btn"):
        st.session_state.confirm_next = True

    if st.session_state.confirm_next:
        st.warning("Would you like another problem?")
        yes_col, no_col = st.columns([1, 1])
        with yes_col:
            if st.button("Yes", key="confirm_next_yes"):
                # Record attempt for current problem (correct only if solved).
                if st.session_state.attempt_recorded_for_problem_id != problem.get("id"):
                    attempt_start = st.session_state.attempt_start_ts or time.time()
                    time_spent_seconds = int(time.time() - attempt_start)
                    steps_taken = len(st.session_state.user_steps)
                    correct = bool(solved)
                    user_solution = "\n".join(st.session_state.user_steps)

                    attempt = AttemptRecord(
                        concept_id=selected_concept_id,
                        problem_text=str(problem.get("problem", "")),
                        correct=correct,
                        steps_taken=steps_taken,
                        time_spent_seconds=time_spent_seconds,
                        user_solution=user_solution,
                    )
                    db.record_attempt(user_id=user_id, record=attempt)
                    st.session_state.attempt_recorded_for_problem_id = problem.get("id")

                st.session_state.confirm_next = False
                # Start another problem with same concept/difficulty.
                _start_new_problem()
                st.rerun()
        with no_col:
            if st.button("No", key="confirm_next_no"):
                st.session_state.confirm_next = False
                st.rerun()


if __name__ == "__main__":
    main()

