

import re

import pandas as pd
import streamlit as st

from services.llm_service import analyze_requirement


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="VANAI QA Agent",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Session state
# --------------------------------------------------

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "last_requirement" not in st.session_state:
    st.session_state.last_requirement = ""

if "analysis_error" not in st.session_state:
    st.session_state.analysis_error = None


# --------------------------------------------------
# Premium dark UI styling
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0B1120;
        color: #E5E7EB;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #273449;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    h1, h2, h3 {
        color: #F8FAFC !important;
    }

    .vanai-subtitle {
        color: #94A3B8;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .vanai-card {
        background: linear-gradient(145deg, #172235, #111827);
        border: 1px solid #29374D;
        border-radius: 14px;
        padding: 20px;
        min-height: 120px;
    }

    .vanai-card-label {
        color: #94A3B8;
        font-size: 0.85rem;
        margin-bottom: 10px;
    }

    .vanai-card-value {
        color: #F8FAFC;
        font-size: 1.8rem;
        font-weight: 700;
    }

    .vanai-accent {
        color: #34D399;
    }

    div.stButton > button {
        background-color: #34D399;
        color: #07111F;
        border: none;
        border-radius: 9px;
        min-height: 44px;
        font-weight: 700;
        width: 100%;
    }

    div.stButton > button:hover {
        background-color: #6EE7B7;
        color: #07111F;
    }

    div[data-testid="stTextArea"] textarea {
        background-color: #111827;
        color: #F8FAFC;
        border: 1px solid #334155;
        border-radius: 10px;
    }

    div[data-testid="stDownloadButton"] button {
        border-radius: 9px;
        min-height: 42px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #29374D;
        border-radius: 10px;
        overflow: hidden;
    }

    hr {
        border-color: #29374D;
    }


/* Improve readability across Streamlit components */
.stApp,
[data-testid="stAppViewContainer"] {
    color: #F1F5F9 !important;
}

/* Small text, captions, and helper descriptions */
.stApp [data-testid="stCaptionContainer"],
.stApp .stMarkdown p,
.stApp label,
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stHelp"] {
    color: #CBD5E1 !important;
}

/* Sidebar text */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #D1D5DB !important;
}

/* Text input and text area */
.stApp textarea,
.stApp input {
    color: #F8FAFC !important;
    background-color: #111827 !important;
    caret-color: #34D399 !important;
}

/* Placeholder text */
.stApp textarea::placeholder,
.stApp input::placeholder {
    color: #94A3B8 !important;
    opacity: 1 !important;
}

/* Tabs */
.stApp button[data-baseweb="tab"] {
    color: #CBD5E1 !important;
}

.stApp button[data-baseweb="tab"][aria-selected="true"] {
    color: #6EE7B7 !important;
}

/* Make secondary text inside metric cards brighter */
.vanai-card-label {
    color: #CBD5E1 !important;
}

/* Table text */
.stApp [data-testid="stDataFrame"] {
    color: #F1F5F9 !important;
}

/* Links */
.stApp a {
    color: #6EE7B7 !important;
}

/* Checkbox labels */
.stApp [data-testid="stCheckbox"] label p {
    color: #E2E8F0 !important;
}

    
/* Remove Streamlit's default header strip */
[data-testid="stHeader"] {
    background: transparent !important;
}

/* Hide the top toolbar decoration */
[data-testid="stToolbar"] {
    background: transparent !important;
}

/* Remove any white border from the header */
[data-testid="stHeader"],
[data-testid="stAppViewContainer"] {
    border-top: none !important;
    box-shadow: none !important;
}

/* Give the page header more breathing room */
.block-container {
    padding-top: 1.5rem !important;
}

/* Premium title styling */
h1 {
    letter-spacing: -0.8px;
    font-weight: 750 !important;
}

/* Refined subtitle */
.vanai-subtitle {
    color: #A8B7CC !important;
    font-size: 1rem;
    line-height: 1.7;
    max-width: 780px;
}

/* Softer section separators */
.stApp hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(
        90deg,
        rgba(52, 211, 153, 0.45),
        rgba(51, 65, 85, 0.65),
        transparent
    ) !important;
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
}

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Helpers for extracting summary data from the report
# --------------------------------------------------

def extract_risk_score(report):
    patterns = [
        r"risk score[^0-9]{0,30}([1-5])\s*(?:/|out of)\s*5",
        r"([1-5])\s*/\s*5",
    ]

    for pattern in patterns:
        match = re.search(pattern, report, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def extract_test_table(report):
    lines = report.splitlines()

    for index, line in enumerate(lines):
        if "|" not in line:
            continue

        header = [
            cell.strip()
            for cell in line.strip().strip("|").split("|")
        ]
        normalized = [cell.lower() for cell in header]

        if (
            any("test" in cell and "id" in cell for cell in normalized)
            and any("scenario" in cell for cell in normalized)
        ):
            rows = []

            for row_line in lines[index + 1:]:
                if "|" not in row_line:
                    if rows:
                        break
                    continue

                cells = [
                    cell.strip()
                    for cell in row_line.strip().strip("|").split("|")
                ]

                # Ignore Markdown table separator rows.
                if all(
                    re.fullmatch(r":?-{3,}:?", cell.replace(" ", ""))
                    for cell in cells
                ):
                    continue

                if len(cells) != len(header):
                    if rows:
                        break
                    continue

                rows.append(cells)

            if rows:
                return pd.DataFrame(rows, columns=header)

    return pd.DataFrame()


def get_readiness(report):
    text = report.lower()

    if "needs clarification" in text:
        return "Needs clarification"

    if "not ready" in text:
        return "Not ready"

    if "ready for testing" in text:
        return "Ready for testing"

    if "ready for development" in text:
        return "Ready for development"

    return "Reviewed"


def render_metric(label, value, note):
    st.markdown(
        f"""
        <div class="vanai-card">
            <div class="vanai-card-label">{label}</div>
            <div class="vanai-card-value">{value}</div>
            <div class="vanai-card-label">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.markdown("# 🧪 VANAI")
    st.caption("AI QUALITY ENGINEERING")
    st.divider()

    st.markdown("### Workspace")
    st.markdown("📝 Requirement Analyzer")
    st.markdown("📋 Test Case Review")
    st.markdown("📥 Report Export")

    st.divider()

    st.markdown("### Environment")
    st.caption("Gemini API · Free tier")
    st.caption("Python 3.9 compatible")

    preview_mode = st.checkbox(
        "Preview dashboard with sample data",
        value=False,
        help="Displays illustrative data without calling Gemini.",
    )

    st.divider()
    st.caption("VANAI QA Agent · Prototype")


# --------------------------------------------------
# Header
# --------------------------------------------------

header_left, header_right = st.columns([4, 1])

with header_left:
    st.markdown(
        '<h1 style="margin-bottom: 0.2rem;">'
        'Requirement <span style="color:#34D399;">Analyzer</span>'
        '</h1>', unsafe_allow_html=True
    )
    st.markdown(
        '<div class="vanai-subtitle">'
        "Transform product requirements into risk insights, "
        "acceptance questions, and actionable test cases."
        "</div>",
        unsafe_allow_html=True,
    )

with header_right:
    st.markdown(" ")
    st.success("● Workspace ready")


# --------------------------------------------------
# Requirement input
# --------------------------------------------------

st.markdown("### Requirement input")

requirement = st.text_area(
    "Paste a Jira story or requirement",
    height=180,
    placeholder=(
        "As a user, I want to log in with my email and password "
        "so that I can securely access my account..."
    ),
    key="requirement_input",
)

st.caption(
    f"{len(requirement)} characters · "
    "Include acceptance criteria when available."
)

analyze_clicked = st.button(
    "✨  Analyze requirement",
    use_container_width=True,
)


# --------------------------------------------------
# Live analysis
# --------------------------------------------------

if analyze_clicked:
    if not requirement.strip():
        st.warning("Please enter a requirement before analyzing.")
    else:
        st.session_state.analysis_error = None

        try:
            with st.spinner("Reviewing requirement and generating QA insights..."):
                result = analyze_requirement(requirement)

            st.session_state.analysis_result = result
            st.session_state.last_requirement = requirement

        except ValueError as exc:
            st.session_state.analysis_error = str(exc)

        except FileNotFoundError:
            st.session_state.analysis_error = (
                "The QA prompt file is missing. "
                "Please contact the application maintainer."
            )

        except RuntimeError as exc:
            error_text = str(exc)

            if any(
                term in error_text.lower()
                for term in (
                    "429",
                    "quota",
                    "resourceexhausted",
                    "rate limit",
                )
            ):
                st.session_state.analysis_error = (
                    "QUOTA_LIMIT: You've reached your Gemini API "
                    "free-tier request limit. Wait for the quota "
                    "to reset, then try again. No paid access "
                    "has been enabled by this app."
                )
            else:
                st.session_state.analysis_error = error_text

        except Exception as exc:
            print(f"Unexpected error: {type(exc).__name__}: {exc}")
            st.session_state.analysis_error = (
                "An unexpected error occurred. Check the terminal "
                "for details and try again."
            )


# --------------------------------------------------
# Error display
# --------------------------------------------------

error_message = st.session_state.analysis_error

if error_message:
    if error_message.startswith("QUOTA_LIMIT:"):
        st.warning(error_message.replace("QUOTA_LIMIT:", "").strip())
    else:
        st.error(error_message)

    st.caption(
        "Your existing analysis, if any, remains available below."
    )


# --------------------------------------------------
# Results and risk summary
# --------------------------------------------------

report = st.session_state.analysis_result

if preview_mode:
    report = """
## Requirement Summary
A user can log in with an email address and password.

## Risk Score
4/5 — Elevated risk due to authentication and account security.

## Overall QA Recommendation
Needs clarification.

## Suggested Test Cases

| Test ID | Scenario | Preconditions | Test Steps | Expected Result | Priority | Type |
|---|---|---|---|---|---|---|
| TC-001 | Valid login | Registered user | Enter valid credentials | User logs in | High | Positive |
| TC-002 | Invalid password | Registered user | Enter incorrect password | Error is displayed | High | Negative |
| TC-003 | Empty fields | Login page open | Submit empty fields | Validation is displayed | Medium | Negative |
| TC-004 | Account security | Repeated failed attempts | Retry invalid login | Security policy is enforced | High | Security |

## Missing or Ambiguous Acceptance Criteria
- Password complexity requirements are not specified.
- Account lockout behavior needs clarification.
- Session timeout behavior is not specified.

## Questions for Product Owner
- What is the account lockout policy?
- Is multi-factor authentication required?

## Overall Recommendation
Needs clarification before release.
"""

if report:
    risk_score = extract_risk_score(report)
    test_df = extract_test_table(report)
    readiness = get_readiness(report)

    st.divider()
    st.markdown("## QA overview")
    st.caption(
        "Preview mode is illustrative. Live mode displays the generated report."
        if preview_mode
        else "Summary metrics extracted from the generated QA analysis."
    )

    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        risk_value = f"{risk_score}/5" if risk_score is not None else "N/A"
        render_metric(
            "RISK SCORE",
            risk_value,
            "Higher score means higher risk",
        )

    with metric2:
        count = len(test_df) if not test_df.empty else 0
        render_metric(
            "TEST CASES",
            str(count),
            "Scenarios found in the report",
        )

    with metric3:
        render_metric(
            "QA READINESS",
            readiness,
            "Based on recommendation text",
        )

    st.divider()

    tab1, tab2 = st.tabs(["📊 Test cases", "📄 Full analysis"])

    with tab1:
        st.markdown("### Suggested test cases")

        if not test_df.empty:
            st.dataframe(
                test_df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                "No Markdown test-case table was detected. "
                "See Full analysis for the complete report."
            )

    with tab2:
        st.markdown("### Full QA report")
        st.markdown(report)

    st.download_button(
        label="⬇️ Download QA report (.md)",
        data=report,
        file_name="vanai_qa_analysis.md",
        mime="text/markdown",
        use_container_width=True,
    )

    if preview_mode:
        st.info(
            "You're viewing sample data. Turn off Preview dashboard "
            "with sample data in the sidebar to return to live analysis."
        )

else:
    st.info(
        "Your QA analysis will appear here. You can also enable "
        "'Preview dashboard with sample data' in the sidebar to "
        "explore the interface without using your Gemini quota."
    )
