import os
import streamlit as st
from dotenv import load_dotenv

from agent.pipeline_agent import PipelineAgent
from memory.hindsight_memory import HindsightMemory
from services.pipeline_service import load_incidents

load_dotenv()

st.set_page_config(
    page_title="PipelineSage",
    page_icon="🧠",
    layout="wide",
)

# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "analyzed_deployment" not in st.session_state:
    st.session_state.analyzed_deployment = None

if "learning_saved" not in st.session_state:
    st.session_state.learning_saved = False


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("🧠 PipelineSage")
st.caption(
    "AI DevOps Pipeline Agent — remembers failures, fixes, "
    "and deployment outcomes."
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.header("⚙️ Configuration")

    hindsight_url = os.getenv(
        "HINDSIGHT_BASE_URL",
        "https://api.hindsight.vectorize.io",
    )

    bank_id = os.getenv(
        "HINDSIGHT_BANK_ID",
        "pipelinesage",
    )

    groq_model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-120b",
    )

    st.write(f"**Hindsight:** `{hindsight_url}`")
    st.write(f"**Memory bank:** `{bank_id}`")
    st.write(f"**LLM:** `{groq_model}`")

    st.divider()

    st.subheader("🧠 Demo workflow")

    st.markdown(
        """
        **1.** Analyze a failure  
        ↓  
        **2.** Recall a similar incident  
        ↓  
        **3.** Recommend a fix  
        ↓  
        **4.** Confirm the outcome  
        ↓  
        **5.** Remember the experience
        """
    )

    st.divider()

    if st.button(
        "📥 Load demo incidents into Hindsight",
        use_container_width=True,
    ):

        try:

            memory = HindsightMemory()
            incidents = load_incidents()

            progress = st.progress(0)

            for i, incident in enumerate(incidents):

                memory.retain_incident(incident)

                progress.progress(
                    (i + 1) / len(incidents)
                )

            st.success(
                f"Retained {len(incidents)} demo incidents."
            )

        except Exception as e:

            st.error(
                f"Could not retain demo incidents: {e}"
            )


# ---------------------------------------------------------
# Load incidents
# ---------------------------------------------------------

incidents = load_incidents()

incident_labels = [
    f"#{x['deployment_id']} — "
    f"{x['service']} — "
    f"{x['status']}"
    for x in incidents
]

selected_label = st.selectbox(
    "Select a pipeline incident",
    incident_labels,
)

selected = incidents[
    incident_labels.index(selected_label)
]


# Reset old analysis when selecting another deployment

if (
    st.session_state.analyzed_deployment
    != selected["deployment_id"]
):

    st.session_state.analysis_result = None
    st.session_state.learning_saved = False


# ---------------------------------------------------------
# Main pipeline event
# ---------------------------------------------------------

st.divider()

left, right = st.columns([1, 1])


with left:

    st.subheader("🚀 Pipeline event")

    st.metric(
        "Deployment",
        f"#{selected['deployment_id']}",
    )

    st.write(
        f"**Service:** `{selected['service']}`"
    )

    st.write(
        f"**Branch:** `{selected['branch']}`"
    )

    st.write(
        f"**Environment:** `{selected['environment']}`"
    )

    st.write(
        f"**Commit:** `{selected['commit']}`"
    )

    if selected["status"] == "FAILED":

        st.error("🔴 DEPLOYMENT FAILED")

    else:

        st.success("🟢 DEPLOYMENT SUCCESSFUL")

    st.code(
        selected["error"],
        language="text",
    )

    analyze = st.button(
        "🔎 Analyze with PipelineSage",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------------------------------
# Analyze button
# ---------------------------------------------------------

if analyze:

    if selected["status"] != "FAILED":

        st.session_state.analysis_result = None

        st.info(
            "Select a failed deployment to run diagnosis."
        )

    else:

        try:

            with st.spinner(
                "🧠 Recalling similar incidents from Hindsight..."
            ):

                agent = PipelineAgent()

                result = agent.analyze_failure(
                    selected
                )

            st.session_state.analysis_result = result
            st.session_state.analyzed_deployment = (
                selected["deployment_id"]
            )

            st.session_state.learning_saved = False

        except Exception as e:

            st.error(
                f"Agent error: {e}"
            )

            st.info(
                "Check GROQ_API_KEY, HINDSIGHT_API_KEY, "
                "HINDSIGHT_BASE_URL, and HINDSIGHT_BANK_ID "
                "in your .env file."
            )


# ---------------------------------------------------------
# Agent analysis
# ---------------------------------------------------------

with right:

    st.subheader("🤖 Agent analysis")

    result = st.session_state.analysis_result

    if result:

        st.success(
            "Historical memory found and analyzed."
        )

        # -------------------------------------------------
        # Memory
        # -------------------------------------------------

        st.markdown(
            "### 🧠 What PipelineSage remembered"
        )

        if result["memories"]:

            for memory in result["memories"]:

                st.info(memory)

        else:

            st.warning(
                "No relevant historical memory was returned."
            )

        # -------------------------------------------------
        # Diagnosis
        # -------------------------------------------------

        st.markdown(
            "### 🔍 Diagnosis"
        )

        st.markdown(
            result["analysis"]
        )

        # -------------------------------------------------
        # Learning loop
        # -------------------------------------------------

        st.divider()

        st.markdown(
            "### 🔄 Learning loop"
        )

        if not st.session_state.learning_saved:

            st.caption(
                "If the recommended fix succeeds, "
                "PipelineSage can retain that outcome "
                "for future deployment failures."
            )

            if st.button(
                "✅ Mark recommended fix as successful",
                use_container_width=True,
            ):

                try:

                    memory = HindsightMemory()

                    outcome = {
                        **selected,
                        "status": "SUCCESS",
                        "resolution": (
                            "Process historical transaction rows "
                            "in batches of 500 records."
                        ),
                        "outcome": (
                            "Human confirmed the recommended resolution "
                            "was successful."
                        ),
                        "learning_source": (
                            "Deployment #1057"
                        ),
                        "related_historical_incident": (
                            "Deployment #1017"
                        ),
                    }

                    memory.retain_incident(
                        outcome
                    )

                    st.session_state.learning_saved = True

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Could not store outcome: {e}"
                    )

        else:

            st.success(
                "🧠 PipelineSage learned from this outcome."
            )

            st.info(
                "The successful resolution has been stored "
                "in Hindsight and can be recalled during "
                "future diagnoses."
            )

            st.markdown(
                """
                **Failure** → **Recommended Fix**
                → **Successful Outcome**
                → **Hindsight Memory**
                """
            )


# ---------------------------------------------------------
# Learning cycle
# ---------------------------------------------------------

st.divider()

st.subheader(
    "🔁 PipelineSage learning cycle"
)

st.markdown(
    """
**Past incident**

`#1017 — migration timeout`

↓

**Successful resolution**

`Batch migration into 500-record batches`

↓

**Hindsight memory**

`Retain → Recall`

↓

**New incident**

`#1057 — similar migration timeout`

↓

**AI recommendation**

`Reuse the previously documented successful approach`

↓

**New outcome**

`Retain the result for future incidents`
"""
)

st.divider()

st.subheader(
    "🧠 Why memory matters"
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "Historical incidents",
    len(incidents),
)

c2.metric(
    "Memory operations",
    "RETAIN + RECALL",
)

c3.metric(
    "Learning loop",
    "Failure → Fix → Outcome",
)

st.caption(
    "PipelineSage is a decision-support prototype. "
    "It recommends troubleshooting actions; a human remains "
    "responsible for production changes."
)