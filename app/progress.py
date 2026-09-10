import streamlit as st

from progress_engine import (
    get_weak_topics,
    get_completed_topics,
    get_in_progress_topics,
)


# =========================================================
# HELPERS
# =========================================================


def calculate_progress_stats(selected_subject: str):

    user_id = str(st.session_state.user_id)
    department = st.session_state.get("user_department")

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


# =========================================================
# CSS
# =========================================================


def inject_progress_css():

    st.markdown(
        """
        <style>

        .progress-title {
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }

        .progress-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 14px;
            margin-bottom: 1rem;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            margin-top: 1rem;
        }

        .metric-box {
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 10px;
            text-align: center;
        }

        .metric-value {
            font-size: 1.1rem;
            font-weight: 700;
        }

        .metric-label {
            font-size: 0.8rem;
            opacity: 0.75;
        }

        .topic-section {
            margin-top: 1rem;
        }

        .topic-pill {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 10px;
            padding: 8px 10px;
            margin-bottom: 8px;
            font-size: 0.88rem;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# COMPONENTS
# =========================================================


def render_metric_cards(weak, completed, in_progress):

    st.markdown(
        f"""
        <div class="metric-grid">

            <div class="metric-box">
                <div class="metric-value">{len(completed)}</div>
                <div class="metric-label">Completed</div>
            </div>

            <div class="metric-box">
                <div class="metric-value">{len(in_progress)}</div>
                <div class="metric-label">Active</div>
            </div>

            <div class="metric-box">
                <div class="metric-value">{len(weak)}</div>
                <div class="metric-label">Weak</div>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# MAIN PANEL
# =========================================================


def render_progress_panel(selected_subject: str):

    inject_progress_css()

    stats = calculate_progress_stats(selected_subject)

    weak = stats["weak"]
    completed = stats["completed"]
    in_progress = stats["in_progress"]
    progress_ratio = stats["progress_ratio"]

    st.markdown(
        """
        <div class="progress-title">
            📈 Progress Tracker
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # PROGRESS CARD
    # =====================================================

    st.markdown('<div class="progress-card">', unsafe_allow_html=True)

    st.progress(progress_ratio)

    st.caption(f"{int(progress_ratio * 100)}% completed")

    render_metric_cards(
        weak,
        completed,
        in_progress,
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # =====================================================
    # WEAK TOPICS
    # =====================================================

    st.markdown("### ⚠️ Weak Topics")

    if weak:

        for topic in weak[:8]:
            st.markdown(
                f"""
                <div class="topic-pill">
                    {topic}
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:
        st.caption("No weak topics yet.")

    # =====================================================
    # COMPLETED TOPICS
    # =====================================================

    with st.expander("✅ Completed Topics"):

        if completed:

            for topic in completed[:10]:
                st.markdown(
                    f"""
                    <div class="topic-pill">
                        {topic}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:
            st.caption("No completed topics yet.")

    # =====================================================
    # ACTIVE TOPICS
    # =====================================================

    with st.expander("📘 In Progress"):

        if in_progress:

            for topic in in_progress[:10]:
                st.markdown(
                    f"""
                    <div class="topic-pill">
                        {topic}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:
            st.caption("No active topics yet.")
