
import streamlit as st

from services.llm_service import analyze_requirement

st.set_page_config(
    page_title="VANAI QA AGENT",
    page_icon="🧪",
    layout="wide"
)

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

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
        st.warning("Please enter a requirement.")

    else:
        try:
            with st.spinner("Analyzing your requirement..."):
                result = analyze_requirement(requirement)

            st.session_state.analysis_result = result

        except ValueError as exc:
            st.warning(str(exc))

        except FileNotFoundError:
            st.error(
                "The QA prompt file is missing. "
                "Please contact the application maintainer."
            )

        except RuntimeError as exc:
            st.error(str(exc))
            st.info(
                "Check your API configuration and network connection, "
                "then try again."
            )

        except Exception as exc:
            print(f"Unexpected error: {type(exc).__name__}: {exc}")
            st.error(
                "An unexpected error occurred while analyzing the requirement. "
                "Check the terminal for details."
            )

if st.session_state.analysis_result:
    st.markdown("## Analysis")
    st.markdown(st.session_state.analysis_result)

    st.download_button(
        label="Download QA Analysis",
        data=st.session_state.analysis_result,
        file_name="vanai_qa_analysis.md",
        mime="text/markdown",
    )
