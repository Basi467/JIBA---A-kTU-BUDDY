import streamlit as st
import sys
from pathlib import Path
from datetime import date, timedelta
import re

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
sys.path.append(str(SRC_DIR))

from ktu_service import KtuService
from progress_engine import get_weak_topics
from app_actions import mark_topic_weak, mark_topic_completed, mark_pyq_solved


def detect_study_plan_intent(text: str) -> bool:
    text = text.lower()
    keywords = [
        "study plan",
        "revision plan",
        "make a plan",
        "create a plan",
        "schedule",
        "timetable",
        "how should i study",
        "plan for exam",
        "days left",
        "exam in",
    ]
    return any(k in text for k in keywords)


def extract_days(text: str):
    text = text.lower()
    m = re.search(r"(\d+)\s+days?", text)
    if m:
        return int(m.group(1))
    m = re.search(r"exam\s+in\s+(\d+)", text)
    if m:
        return int(m.group(1))
    return None


def format_study_plan(plan):
    lines = ["### Study Plan"]
    current_module = None

    for item in plan[:20]:
        if item.module_no != current_module:
            current_module = item.module_no
            lines.append(f"\n**Module {current_module}**")

        lines.append(
            f"- **{item.plan_date}** — {item.topic_name} "
            f"(Priority: {item.priority_label}, Repeated: {item.question_count}, "
            f"Hours: {item.recommended_hours})"
        )

    return "\n".join(lines)


def init_exam_state(selected_subject: str):
    subject_key = f"exam_subject_{selected_subject}"

    if st.session_state.get("exam_state_subject") != subject_key:
        st.session_state.exam_state_subject = subject_key
        st.session_state.exam_teach_queue = []
        st.session_state.exam_teach_index = 0
        st.session_state.exam_pyq_queue = []
        st.session_state.exam_pyq_index = 0


def render_quick_study_plan(
    service: KtuService, user_id: str, selected_subject: str, hours_per_day: float, department: str
):
    with st.expander("Quick Study Plan", expanded=False):
        exam_date = st.date_input(
            "Exam Date",
            value=date.today() + timedelta(days=7),
            min_value=date.today(),
            key=f"exam_mode_date_{selected_subject}",
        )

        if st.button("Generate Study Plan", key=f"exam_mode_plan_btn_{selected_subject}"):
            weak_topics = get_weak_topics(user_id, selected_subject, department=department)
            with st.spinner("Generating study plan..."):
                plan = service.generate_study_plan(
                    subject_name=selected_subject,
                    exam_date=exam_date.isoformat(),
                    hours_per_day=float(hours_per_day),
                    manual_weak_topics=weak_topics,
                )
            st.markdown(format_study_plan(plan))

    plan_request = st.text_input(
        "Quick request",
        placeholder="Example: make me a 4 day plan",
        key=f"exam_mode_request_{selected_subject}",
    )

    if plan_request and detect_study_plan_intent(plan_request):
        days = extract_days(plan_request)
        exam_date = date.today() + timedelta(days=days if days else 7)
        weak_topics = get_weak_topics(user_id, selected_subject, department=department)

        with st.spinner("Generating study plan..."):
            plan = service.generate_study_plan(
                subject_name=selected_subject,
                exam_date=exam_date.isoformat(),
                hours_per_day=float(hours_per_day),
                manual_weak_topics=weak_topics,
            )
        st.markdown(format_study_plan(plan))


def render_exam_overview(service: KtuService, selected_subject: str, user_id: str, department: str):
    exam_data = service.get_exam_mode(selected_subject)

    if not exam_data:
        st.warning(f"No exam data available for {selected_subject}")
        return

    for module in exam_data:
        st.markdown(f"## Module {module.module_no}")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("**High Priority Topics**")
            if module.high_priority_topics:
                for t in module.high_priority_topics[:6]:
                    col_a, col_b, col_c = st.columns([5, 1, 1])
                    with col_a:
                        st.write(f"- {t}")

            else:
                st.caption("No high priority topics.")

        with c2:
            st.markdown("**Medium Priority Topics**")
            if module.medium_priority_topics:
                for t in module.medium_priority_topics[:6]:
                    st.write(f"- {t}")
            else:
                st.caption("No medium priority topics.")

        with c3:
            st.markdown("**Low Priority Topics**")
            if module.low_priority_topics:
                for t in module.low_priority_topics[:6]:
                    st.write(f"- {t}")
            else:
                st.caption("No low priority topics.")

        st.markdown("### Repeated Questions")
        if module.repeated_questions:
            for idx, q in enumerate(module.repeated_questions[:6]):
                qcol1, qcol2, qcol3 = st.columns([6, 1, 1])

                with qcol1:
                    st.write(f"**[{q.year}] ({q.marks} marks)** {q.question_text}")
                    if q.topic_name:
                        st.caption(f"Topic: {q.topic_name}")

                with qcol2:
                    if q.topic_name and st.button(
                        "Solved",
                        key=f"solved_{selected_subject}_{module.module_no}_{idx}"
                    ):
                        status = mark_pyq_solved(user_id, selected_subject, q.topic_name, department=department)
                        st.success(f"{q.topic_name} -> {status}")
                        st.rerun()

                with qcol3:
                    if q.topic_name and st.button(
                        "Weak",
                        key=f"qweak_{selected_subject}_{module.module_no}_{idx}"
                    ):
                        status = mark_topic_weak(user_id, selected_subject, q.topic_name, department=department)
                        st.warning(f"{q.topic_name} -> {status}")
                        st.rerun()
        else:
            st.caption("No repeated questions found.")

        st.markdown("---")


def render_teach_high_priority(service: KtuService, selected_subject: str, user_id: str, department: str):
    if not st.session_state.exam_teach_queue:
        if st.button("Start Teaching High Priority Topics", key=f"start_teach_{selected_subject}"):
            st.session_state.exam_teach_queue = service.get_high_priority_teach_queue(selected_subject)
            st.session_state.exam_teach_index = 0
            st.rerun()
        st.info("Start a guided flow to learn one high-priority topic at a time.")
        return

    queue = st.session_state.exam_teach_queue
    idx = st.session_state.exam_teach_index

    if idx >= len(queue):
        st.success("You completed all high-priority topics.")
        if st.button("Restart Teaching Queue", key=f"restart_teach_{selected_subject}"):
            st.session_state.exam_teach_index = 0
            st.rerun()
        return

    item = queue[idx]

    st.markdown(f"## 📘 {item.topic_name}")
    st.caption(
        f"Module {item.module_no} • Priority: {item.priority_label} • "
        f"Repeated: {item.question_count or 0}"
    )

    with st.spinner("Preparing lesson..."):
        lesson = service.teach_topic(
            subject_name=selected_subject,
            topic_name=item.topic_name,
        )

    st.markdown("### Simple Explanation")
    st.write(lesson.get("simple_explanation", ""))

    st.markdown("### Exam-Ready Answer")
    st.write(lesson.get("exam_answer", ""))

    key_points = lesson.get("key_points", [])
    if key_points:
        st.markdown("### Key Points")
        for point in key_points:
            st.markdown(f"- {point}")

    if lesson.get("memory_tip"):
        st.markdown("### Memory Tip")
        st.info(lesson["memory_tip"])

    pyqs = lesson.get("related_pyqs", [])
    if pyqs:
        st.markdown("### Related PYQs")
        for q in pyqs:
            st.markdown(f"- **[{q.year}] ({q.marks} marks)** {q.question_text}")

    if lesson.get("practice_question"):
        st.markdown("### Practice Question")
        st.write(lesson["practice_question"])

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("Weak", key=f"teach_weak_{selected_subject}_{idx}"):
            status = mark_topic_weak(user_id, selected_subject, item.topic_name, department=department)
            st.warning(f"{item.topic_name} -> {status}")
            st.session_state.exam_teach_index += 1
            st.rerun()

    with c2:
        if st.button("Done", key=f"teach_done_{selected_subject}_{idx}"):
            status = mark_topic_completed(user_id, selected_subject, item.topic_name, department=department)
            st.success(f"{item.topic_name} -> {status}")
            st.session_state.exam_teach_index += 1
            st.rerun()

    with c3:
        if st.button("Next Topic", key=f"teach_next_{selected_subject}_{idx}"):
            st.session_state.exam_teach_index += 1
            st.rerun()

    with c4:
        if st.button("Restart", key=f"teach_restart_btn_{selected_subject}_{idx}"):
            st.session_state.exam_teach_index = 0
            st.rerun()


def render_solve_repeated_pyqs(service: KtuService, selected_subject: str, user_id: str, department: str):
    if not st.session_state.exam_pyq_queue:
        if st.button("Start Solving Repeated PYQs", key=f"start_pyq_{selected_subject}"):
            st.session_state.exam_pyq_queue = service.get_repeated_question_queue(
                selected_subject,
                limit_per_module=4,
            )
            st.session_state.exam_pyq_index = 0
            st.rerun()
        st.info("Start a guided flow to answer repeated questions one by one.")
        return

    queue = st.session_state.exam_pyq_queue
    idx = st.session_state.exam_pyq_index

    if idx >= len(queue):
        st.success("You completed all repeated-question practice items.")
        if st.button("Restart PYQ Queue", key=f"restart_pyq_{selected_subject}"):
            st.session_state.exam_pyq_index = 0
            st.rerun()
        return

    item = queue[idx]

    st.markdown("## ✍️ PYQ Practice")
    st.caption(
        f"Module {item.module_no} • Year: {item.year} • Marks: {item.marks} • Topic: {item.topic_name or 'Unknown'}"
    )

    st.markdown("### Question")
    st.write(item.question_text)

    with st.spinner("Generating exam-style answer..."):
        answer = service.answer_exam_question(
            subject_name=selected_subject,
            question_text=item.question_text,
            topic_name=item.topic_name,
        )

    st.markdown("### Exam-Style Answer")
    st.write(answer)

    c1, c2, c3 = st.columns(3)

    with c1:
        if item.topic_name and st.button("Solved", key=f"pyq_solved_{selected_subject}_{idx}"):
            status = mark_pyq_solved(user_id, selected_subject, item.topic_name, department=department)
            st.success(f"{item.topic_name} -> {status}")
            st.session_state.exam_pyq_index += 1
            st.rerun()

    with c2:
        if item.topic_name and st.button("Weak", key=f"pyq_weak_{selected_subject}_{idx}"):
            status = mark_topic_weak(user_id, selected_subject, item.topic_name, department=department)
            st.warning(f"{item.topic_name} -> {status}")
            st.session_state.exam_pyq_index += 1
            st.rerun()

    with c3:
        if st.button("Next Question", key=f"pyq_next_{selected_subject}_{idx}"):
            st.session_state.exam_pyq_index += 1
            st.rerun()


def render_exam_mode_ui(selected_subject: str, hours_per_day: float = 3.0):
    user_id = str(st.session_state.user_id)
    department = st.session_state.user_department
    service = KtuService(user_id=user_id, department=department)

    init_exam_state(selected_subject)

    st.subheader("Exam Mode")
    st.caption("Module-wise important topics, repeated questions, and guided exam prep.")

    render_quick_study_plan(service, user_id, selected_subject, hours_per_day, department)

    mode = st.radio(
        "Exam Tools",
        ["Overview", "Teach High Priority", "Solve Repeated PYQs"],
        horizontal=True,
        key=f"exam_tools_{selected_subject}",
    )

    st.divider()

    if mode == "Overview":
        render_exam_overview(service, selected_subject, user_id, department)
    elif mode == "Teach High Priority":
        render_teach_high_priority(service, selected_subject, user_id, department)
    else:
        render_solve_repeated_pyqs(service, selected_subject, user_id, department)