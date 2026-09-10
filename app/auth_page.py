import streamlit as st
import sys
from pathlib import Path

# Project paths
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
APP_DIR = ROOT_DIR / "app"
sys.path.append(str(SRC_DIR))

from auth_engine import register_user, login_user
from session_store import save_session, clear_session


SCHEME_OPTIONS = ["KTU_2019", "KTU_2024"]
DEPARTMENT_OPTIONS = ["CSE", "AI&DS", "EEE", "EC", "ME", "CIVIL"]
SEMESTER_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8]

LOGO_PATH = APP_DIR / "logo.png"


def init_auth_state():
    defaults = {
        "is_authenticated": False,
        "user_id": None,
        "user_name": None,
        "user_email": None,
        "user_scheme": None,
        "user_department": None,
        "user_semester": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_logged_in_user(user_row):
    st.session_state.is_authenticated = True
    st.session_state.user_id = user_row["id"]
    st.session_state.user_name = user_row["name"]
    st.session_state.user_email = user_row["email"]
    st.session_state.user_scheme = user_row["scheme"]
    st.session_state.user_department = user_row["department"]
    st.session_state.user_semester = user_row["semester"]


def logout():
    clear_session()
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def render_brand_header():
    col_logo, col_text = st.columns([1, 4], vertical_alignment="center")

    with col_logo:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=80)

    with col_text:
        st.markdown(
            """
            <div style="padding-left: 0.25rem;">
                <h2 style="margin: 0; padding: 0; line-height: 1.2;">KTU Buddy</h2>
                <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">
                    Personalized AI study assistant for KTU students
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()


def register_form():
    st.markdown("#### Create account")
    st.caption("Set up your profile to get your subjects and study support.")

    with st.form("register_form", clear_on_submit=False):
        name = st.text_input("Full Name", placeholder="Enter your name")
        email = st.text_input("Email", placeholder="Enter your email")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Minimum 6 characters",
            )
        with col_p2:
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter password",
            )

        st.markdown("##### Academic Profile")
        col1, col2, col3 = st.columns(3)
        with col1:
            scheme = st.selectbox("Scheme", SCHEME_OPTIONS)
        with col2:
            department = st.selectbox("Department", DEPARTMENT_OPTIONS)
        with col3:
            semester = st.selectbox("Semester", SEMESTER_OPTIONS)

        st.write("")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Name is required.")
            return
        if not email.strip():
            st.error("Email is required.")
            return
        if not password:
            st.error("Password is required.")
            return
        if len(password) < 6:
            st.error("Password must be at least 6 characters.")
            return
        if password != confirm_password:
            st.error("Passwords do not match.")
            return

        try:
            user_id = register_user(
                name=name.strip(),
                email=email.strip(),
                password=password,
                scheme=scheme,
                department=department,
                semester=int(semester),
            )
            st.success(
                f"Account created. Your user ID is **{user_id}**. Please log in."
            )
        except Exception as e:
            st.error(f"Registration failed: {e}")


def login_form():
    st.markdown("#### Welcome back")
    st.caption("Log in to continue your study session.")

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input(
            "Password", type="password", placeholder="Enter your password"
        )
        st.write("")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        if not email.strip() or not password:
            st.error("Enter email and password.")
            return

        user = login_user(email=email.strip(), password=password)
        if user is None:
            st.error("Invalid email or password.")
            return

        set_logged_in_user(user)
        save_session(user["id"])
        st.rerun()


def user_profile_card():
    st.markdown("#### Your Profile")
    st.caption("You are currently logged in.")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name**  \n{st.session_state.user_name}")
            st.markdown(f"**Email**  \n{st.session_state.user_email}")
            st.markdown(f"**Scheme**  \n{st.session_state.user_scheme}")
        with col2:
            st.markdown(f"**Department**  \n{st.session_state.user_department}")
            st.markdown(f"**Semester**  \n{st.session_state.user_semester}")

    st.write("")
    if st.button("Logout", use_container_width=True):
        logout()
        st.rerun()


def render_auth_page():
    init_auth_state()

    st.set_page_config(
        page_title="KTU Buddy",
        page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "📚",
        layout="centered",
    )

    # Inject minimal CSS — tighten default Streamlit padding only
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 2.2, 1])

    with center:
        render_brand_header()

        if st.session_state.is_authenticated:
            user_profile_card()
            return

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.write("")
            login_form()

        with tab2:
            st.write("")
            register_form()


if __name__ == "__main__":
    render_auth_page()