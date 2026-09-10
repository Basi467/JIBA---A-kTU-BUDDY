import streamlit as st
import sys
from pathlib import Path
from datetime import date, timedelta
import re

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
sys.path.append(str(SRC_DIR))

from ktu_service import KtuService
from context_manager import (
    get_or_create_session,
    get_chat_history
)
from progress_engine import get_weak_topics


# =========================================================
# STATE
# =========================================================

def init_tutor_state():

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    if "last_plan" not in st.session_state:
        st.session_state.last_plan = None


# =========================================================
# HELPERS
# =========================================================

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

    m = re.search(r"(\\d+)\\s+days?", text)

    if m:
        return int(m.group(1))

    m = re.search(r"exam\\s+in\\s+(\\d+)", text)

    if m:
        return int(m.group(1))

    return None


def format_study_plan(plan):

    lines = ["### Study Plan"]

    current_module = None

    for item in plan[:20]:

        if item.module_no != current_module:

            current_module = item.module_no

            lines.append(
                f"\n**Module {current_module}**"
            )

        lines.append(
            f"- **{item.plan_date}** — "
            f"{item.topic_name} "
            f"(Priority: {item.priority_label}, "
            f"Repeated: {item.question_count}, "
            f"Hours: {item.recommended_hours})"
        )

    return "\n".join(lines)


# =========================================================
# MAIN UI
# =========================================================

def render_tutor_chat_only(
    selected_subject: str,
    hours_per_day: float = 3.0
):

    # =====================================================
    # CSS
    # =====================================================

    st.markdown("""
    <style>

    /* =====================================================
       CHAT CONTAINER
    ===================================================== */

    [data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    [data-testid="stVerticalBlock"] {
        border: none !important;
        box-shadow: none !important;
    }

    /* =====================================================
       CHAT INPUT
    ===================================================== */

    div[data-testid="stChatInput"] {

        position: fixed;

        bottom: 10px;

        left: 290px;

        right: 340px;

        z-index: 999;

        background: transparent;
    }

    /* =====================================================
       INPUT TEXTAREA
    ===================================================== */

    div[data-testid="stChatInput"] textarea {

        border-radius: 18px !important;

        border: 1px solid rgba(0,0,0,0.08) !important;

        background: white !important;

        color: black !important;

        padding-top: 1rem !important;
        padding-bottom: 1rem !important;

        padding-left: 1rem !important;
        padding-right: 1rem !important;

        font-size: 1rem !important;

        box-shadow:
            0 4px 18px rgba(0,0,0,0.12) !important;
    }

    /* =====================================================
       CHAT MESSAGE SPACING
    ===================================================== */

    div[data-testid="stChatMessage"] {

        border: none !important;

        background: transparent !important;

        margin-bottom: 1rem !important;
    }

    /* =====================================================
       CHAT AREA PADDING
    ===================================================== */

    .chat-bottom-space {
        height: 120px;
    }

    </style>
    """, unsafe_allow_html=True)

    # =====================================================
    # STATE
    # =====================================================

    init_tutor_state()

    user_id = str(st.session_state.user_id)
    department = st.session_state.user_department

    service = KtuService(user_id=user_id, department=department)

    session_id = get_or_create_session(
        user_id,
        selected_subject,
        department=department,
    )

    history = get_chat_history(session_id)

    if (
        not st.session_state.chat_messages
        and history
    ):
        st.session_state.chat_messages = history

    # =====================================================
    # CHAT CONTAINER
    # =====================================================

    chat_container = st.container(
        height=650,
        border=False
    )

    # =====================================================
    # CHAT HISTORY
    # =====================================================

    with chat_container:

        for msg in st.session_state.chat_messages:

            with st.chat_message(msg["role"]):

                st.markdown(msg["content"])

    # =====================================================
    # BOTTOM SPACING
    # =====================================================

    st.markdown(
        "<div class='chat-bottom-space'></div>",
        unsafe_allow_html=True
    )

    # =====================================================
    # CHAT INPUT
    # =====================================================

    prompt = st.chat_input(
        f"Ask anything from {selected_subject}"
    )

    # =====================================================
    # USER PROMPT
    # =====================================================

    if prompt:

    # =========================================
    # SHOW USER MESSAGE IMMEDIATELY
    # =========================================

        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Save to history
        st.session_state.chat_messages.append({
            "role": "user",
            "content": prompt
        })

        # =========================================
        # ASSISTANT RESPONSE
        # =========================================

        with chat_container:
            with st.chat_message("assistant"):

                # ---------------------------------
                # STUDY PLAN
                # ---------------------------------

                if detect_study_plan_intent(prompt):

                    days = extract_days(prompt)

                    exam_date = date.today() + timedelta(
                        days=days if days else 7
                    )

                    weak_topics = get_weak_topics(
                        user_id,
                        selected_subject,
                        department=department,
                    )

                    with st.spinner(
                        "Generating study plan..."
                    ):

                        plan = service.generate_study_plan(
                            subject_name=selected_subject,
                            exam_date=exam_date.isoformat(),
                            hours_per_day=float(hours_per_day),
                            manual_weak_topics=weak_topics,
                        )

                    st.session_state.last_plan = plan

                    reply = format_study_plan(plan)

                # ---------------------------------
                # NORMAL CHAT
                # ---------------------------------

                else:

                    with st.spinner("Thinking..."):

                        reply = service.ask_tutor(
                            subject_name=selected_subject,
                            question=prompt,
                            topic_name=None,
                        )

                st.markdown(reply)

        # Save assistant message
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": reply
        })

        st.rerun()