import streamlit as st
import sqlite3
import sys
import html
from pathlib import Path
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
APP_DIR = ROOT_DIR / "app"
sys.path.append(str(SRC_DIR))
sys.path.append(str(APP_DIR))
import streamlit.components.v1 as components
from auth_page import render_auth_page, logout
from auth_engine import get_subjects_for_user, get_user_by_id
from session_store import load_session
from tutor_mode import render_tutor_chat_only
from exam_mode_ui import render_exam_mode_ui
from progress_engine import (
    get_weak_topics,
    get_completed_topics,
    get_in_progress_topics,
)
from module_topic_priority_engine import preview_subject

DB_PATH = ROOT_DIR / "database" / "ktu.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

import base64

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
    
def restore_user_session():
    saved_user_id = load_session()
    if not saved_user_id:
        return

    user = get_user_by_id(saved_user_id)
    if not user:
        return

    st.session_state.is_authenticated = True
    st.session_state.user_id = user["id"]
    st.session_state.user_name = user["name"]
    st.session_state.user_email = user["email"]
    st.session_state.user_scheme = user["scheme"]
    st.session_state.user_department = user["department"]
    st.session_state.user_semester = user["semester"]


def init_state():
    defaults = {
        "is_authenticated": False,
        "user_id": None,
        "user_name": None,
        "user_email": None,
        "user_scheme": None,
        "user_department": None,
        "user_semester": None,
        "selected_subject": None,
        "last_subject": None,
        "exam_mode": False,
        "hours_per_day": 3.0,
        "chat_messages": [],
        "last_plan": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state.is_authenticated:
        restore_user_session()


def reset_subject_state_on_change(new_subject: str):
    if st.session_state.last_subject is None:
        st.session_state.last_subject = new_subject
        return

    if st.session_state.last_subject != new_subject:
        st.session_state.last_subject = new_subject
        st.session_state.chat_messages = []
        st.session_state.last_plan = None

        # reset exam mode internal teaching queues if present
        st.session_state.exam_teach_queue = []
        st.session_state.exam_teach_index = 0
        st.session_state.exam_pyq_queue = []
        st.session_state.exam_pyq_index = 0


def subject_selector(user_id: int):
    subjects = get_subjects_for_user(user_id)

    if not subjects:
        st.warning("No subjects found for your profile.")
        return None

    subject_names = [s["subject_name"] for s in subjects]

    if not subject_names:
        st.warning("No subjects available.")
        return None

    if st.session_state.selected_subject not in subject_names:
        st.session_state.selected_subject = subject_names[0]

    selected_subject = st.sidebar.selectbox(
        "Select Subject",
        subject_names,
        index=subject_names.index(st.session_state.selected_subject),
    )

    reset_subject_state_on_change(selected_subject)
    st.session_state.selected_subject = selected_subject
    return selected_subject

def render_profile_sidebar():

    safe_name = html.escape(str(st.session_state.user_name or ""))
    safe_department = html.escape(str(st.session_state.user_department or ""))
    safe_semester = html.escape(str(st.session_state.user_semester or ""))
    safe_scheme = html.escape(str(st.session_state.user_scheme or ""))

    profile_html = f"""
    <div style="
        background: rgba(255,255,255,0.06);
        padding: 12px;
        border-radius: 12px;
        font-family: sans-serif;
        color: #636363;
        line-height: 1.5;
    ">
    <div  style="font-size: 20px; font-weight: bold; margin-bottom: 8px; color: #222222;"> 👤 PROFILE </div>

        <div style="
            font-size: 18px;
            font-weight: 100px;
            margin-bottom: 4px;
        ">
            Name: {safe_name}
        </div>

        <div style = "font-size: 14px; font-weight: 100px; margin-bottom: 1px;">
            Department: {safe_department}
        </div>

        <div style = "font-size: 14px; font-weight: 100px; margin-bottom: 1px;">
            Semester: {safe_semester},{safe_scheme}
    </div>
    """

    with st.sidebar:
        components.html(profile_html, height=140)
def render_controls_sidebar():
    st.sidebar.markdown("---")
    st.sidebar.markdown("Settings")

    st.session_state.exam_mode = st.sidebar.toggle(
        "Exam Mode",
        value=st.session_state.exam_mode,
    )

    st.session_state.hours_per_day = st.sidebar.slider(
        "Hours Per Day",
        min_value=1.0,
        max_value=24.0,
        value=float(st.session_state.hours_per_day),
        step=0.5,
    )

    st.sidebar.markdown("---")

    if st.sidebar.button("Logout", use_container_width=True):
        logout()
        st.rerun()


def left_sidebar():
        logo_base64 = get_base64_image(str(APP_DIR / "logo.png"))

        st.sidebar.markdown(
            f"""
            <style>
            .sidebar-header {{
                display: flex;
                align-items: center;
                gap: 8px;
                padding-top: 1px;
                padding-bottom: 1px;
            }}

            .sidebar-header img {{
                width: 100px;
                height: 100px;
                border-radius: 20px;
            }}

            .sidebar-title {{
                font-size: 22px;
                font-weight: 700;
                color:#05014a;
                line-height: 1.1;
            }}
            </style>

            <div class="sidebar-header">
                <img src="data:image/png;base64,{logo_base64}">
                <div class="sidebar-title">
                    JIBA A<br>KTU Buddy
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        #st.sidebar.markdown("---")

        render_profile_sidebar()
        render_controls_sidebar()
def calculate_progress_stats(selected_subject: str):
    user_id = str(st.session_state.user_id)
    department = st.session_state.user_department

    weak = get_weak_topics(user_id, selected_subject, department=department)
    completed = get_completed_topics(user_id, selected_subject, department=department)
    in_progress = get_in_progress_topics(user_id, selected_subject, department=department)

    unique_topics = set(weak + completed + in_progress)
    total_tracked = len(unique_topics)

    if total_tracked > 0:
        progress_ratio = len(completed) / total_tracked
    else:
        progress_ratio = 0.0

    return {
        "weak": weak,
        "completed": completed,
        "in_progress": in_progress,
        "progress_ratio": progress_ratio,
        "total_tracked": total_tracked,
    }


def render_right_progress_panel(selected_subject: str):
    stats = calculate_progress_stats(selected_subject)

    weak = stats["weak"]
    completed = stats["completed"]
    in_progress = stats["in_progress"]
    progress_ratio = stats["progress_ratio"]

    st.markdown("### Progress")
    st.progress(progress_ratio)
    st.caption(f"{int(progress_ratio * 100)}% completed")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Weak", len(weak))
    with c2:
        st.metric("Done", len(completed))
    with c3:
        st.metric("Active", len(in_progress))

    st.markdown("---")

    with st.expander(" Weak Topics", expanded=True):
        if weak:
            for t in weak[:10]:
                st.write(f"- {t}")
        else:
            st.caption("No weak topics yet.")

    with st.expander(" Completed Topics", expanded=False):
        if completed:
            for t in completed[:10]:
                st.write(f"- {t}")
        else:
            st.caption("No completed topics yet.")

    with st.expander(" In Progress", expanded=False):
        if in_progress:
            for t in in_progress[:10]:
                st.write(f"- {t}")
        else:
            st.caption("No in-progress topics yet.")

    render_predicted_topics_panel(selected_subject)


def render_predicted_topics_panel(selected_subject: str):
    """Show topics ranked 'High' priority within their module, based on
    past-year question frequency/marks (see module_topic_priority_engine.py)."""
    try:
        priorities = preview_subject(selected_subject, department=st.session_state.user_department)
    except sqlite3.OperationalError:
        return

    high_priority = [p for p in priorities if p.priority_label == "High"]

    with st.expander("🎯 Predicted High-Priority Topics", expanded=False):
        if not high_priority:
            st.caption("Not enough past-year question data for this subject yet.")
            return

        current_module = None
        for item in high_priority[:15]:
            if item.module_no != current_module:
                current_module = item.module_no
                st.markdown(f"**Module {current_module}**")
            st.write(f"- {item.topic_name}  ·  asked {item.question_count}x")


def render_main_area(selected_subject: str):

    if st.session_state.exam_mode:
        render_exam_mode_ui(
            selected_subject=selected_subject,
            hours_per_day=float(st.session_state.hours_per_day),
        )
    else:
        render_tutor_chat_only(
            selected_subject=selected_subject,
            hours_per_day=float(st.session_state.hours_per_day),
        )


def show_dashboard():

    left_sidebar()

    subjects = get_subjects_for_user(
        st.session_state.user_id
    )

    if not subjects:
        st.info("No subjects found.")
        return

    # Subject list
    subject_names = [
        s["subject_name"]
        for s in subjects
    ]

    # Default subject
    if (
        st.session_state.selected_subject
        not in subject_names
    ):
        st.session_state.selected_subject = (
            subject_names[0]
        )

    selected_subject = (
        st.session_state.selected_subject
    )

    # =====================================================
    # MAIN AREA
    # =====================================================

    main_col, right_col = st.columns(
        [3.6, 1.2],
        gap="large"
    )

    with main_col:

        render_main_area(
            selected_subject
        )

    # =====================================================
    # RIGHT PANEL
    # =====================================================

    with right_col:

        # Subject selector moved here
        selected_subject = st.selectbox(
            "Subject",
            subject_names,
            index=subject_names.index(
                st.session_state.selected_subject
            )
        )

        st.session_state.selected_subject = (
            selected_subject
        )

        render_right_progress_panel(
            selected_subject
        )

def main():
    st.set_page_config(
        page_title="KTU Buddy",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Hide Streamlit toolbar + menu + footer
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Optional: hide deploy button */
        .stDeployButton {
            display: none;
        }
        .st-emotion-cache-10p9htt e9ic3ti4 {
                margin-top: 0px;}

        /* Floating right panel */
.floating-progress {
    position: sticky;
    top: 20px;

    background: rgba(255,255,255,0.04);

    padding: 16px;
    border-radius: 16px;

    border: 1px solid rgba(255,255,255,0.08);
}
                /* Remove top padding from whole page */
.block-container {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}

/* Remove sidebar top spacing */
[data-testid="stSidebar"] {
    padding-top: 0rem !important;
}

/* Remove sidebar inner spacing */
[data-testid="stSidebarUserContent"] {
    padding-top: 0rem !important;
}

/* Remove toolbar */
[data-testid="stToolbar"] {
    display: none;
}

/* Remove decoration */
[data-testid="stDecoration"] {
    display: none;
}

[data-testid="stSidebar"] {
    padding-top: 0rem !important;
}

/* Sidebar inner container */
[data-testid="stSidebarUserContent"] {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}

/* Remove extra sidebar block spacing */
[data-testid="stSidebar"] .block-container {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}
        </style>
    """, unsafe_allow_html=True)

    init_state()

    if not st.session_state.is_authenticated:
        render_auth_page()
        return

    show_dashboard()


if __name__ == "__main__":
    main()