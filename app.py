import streamlit as st

from services.llm_service import (
    analyze_requirement
)

st.set_page_config(
    page_title="VANAI QA AGENT",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 VANAI QA AGENT")

st.write(
    """
    Paste a Jira Story or Requirement
    and receive QA analysis.
    """
)

requirement = st.text_area(
    "Requirement",
    height=250
)

if st.button("Analyze Requirement"):

    if not requirement.strip():
        st.warning(
            "Please enter a requirement."
        )

    else:

        with st.spinner(
            "Analyzing..."
        ):
            result = analyze_requirement(
                requirement
            )

        st.markdown("## Analysis")

        st.markdown(result)