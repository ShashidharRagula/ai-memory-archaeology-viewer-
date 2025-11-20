import streamlit as st
from datetime import date

from main_memory_engine import run_engine_for_date


# ---------- BASIC PAGE CONFIG & LIGHT CSS ----------
st.set_page_config(
    page_title="AI Memory Archaeology",
    page_icon="🧠",
    layout="wide",
)

# Simple background + font tweaks
st.markdown(
    """
    <style>
    /* Make main background slightly gray */
    .stApp {
        background-color: #f5f7fb;
    }
    /* Tweak card-like containers */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- SIDEBAR ----------
st.sidebar.title("Settings")

selected_date = st.sidebar.date_input(
    "Choose a date",
    value=date(2025, 1, 1),
)

gap_minutes = st.sidebar.slider(
    "Gap between sessions (minutes)",
    min_value=15,
    max_value=180,
    value=60,
    step=15,
)

if st.sidebar.button("Generate memory story"):
    with st.spinner("Reconstructing the day..."):
        output = run_engine_for_date(selected_date, data_dir="data", gap_minutes=gap_minutes)

    # ---------- HEADER ----------
    st.markdown("### 🧠 AI Memory Archaeology Viewer")
    st.caption("Reconstructing a gentle memory story from daily phone data.")

    # ---------- TOP METRICS + SOURCE COUNTS ----------
    st.markdown(f"#### Overview for {output['target_date'].isoformat()}")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.metric("Total events (this day)", output["total_events"])
    with col2:
        st.metric("Number of sessions", output["num_sessions"])
    with col3:
        with st.expander("Per-source event counts", expanded=False):
            for source, count in output.get("per_source_counts", {}).items():
                st.write(f"- **{source}**: {count}")

    st.markdown("---")

    # ---------- MEMORY STORY SECTION ----------
    st.subheader("📖 Memory Story (AI)")
    st.write(output["memory_story"])

    st.markdown("---")

    # ---------- CAREGIVER SUMMARY SECTION ----------
    st.subheader("🧑‍⚕️ Caregiver Summary (AI)")
    for line in output["caregiver_summary"].splitlines():
        if line.strip():
            st.write(line)

else:
    # Landing view before clicking the button
    st.markdown("### 🧠 AI Memory Archaeology Viewer")
    st.caption("Reconstructing a gentle memory story from daily phone data.")
    st.info(
        "Select a date in the sidebar and click **Generate memory story** "
        "to view the reconstructed story and caregiver summary."
    )


