import streamlit as st

from services.llm_service import (
    analyze_requirement
)

st.set_page_config(
    page_title="AI QA Requirement Analyzer",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 AI QA Requirement Analyzer")

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