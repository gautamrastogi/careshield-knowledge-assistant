import json
import pathlib
import typing

import streamlit as st

from careshield import contracts, pipeline

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLE_PATH = ROOT / "examples" / "synthetic-care-report.md"


class UploadedFileLike(typing.Protocol):
    """Minimal runtime shape needed from Streamlit uploads."""

    name: str

    def getvalue(self) -> bytes:
        """Return uploaded file bytes.

        :return: Uploaded file bytes.
        """
        raise NotImplementedError


def main() -> None:
    """Run the Streamlit learning UI."""
    st.set_page_config(page_title="CareShield", page_icon="🛡️", layout="wide")
    st.title("CareShield Knowledge Assistant")
    st.caption("Synthetic, public-safe GenAI/RAG learning app")

    left, right = st.columns([0.42, 0.58], gap="large")
    with left:
        mode = st.radio(
            label="Flow",
            options=["Built-in policy Q&A", "Document analysis"],
            horizontal=True,
        )
        role = st.selectbox(
            label="Role",
            options=[item.value for item in contracts.schema.Role],
            index=[item.value for item in contracts.schema.Role].index(contracts.schema.Role.nurse.value),
        )
        question = st.text_area(
            label="Question",
            value="What must be redacted before vendor sharing?",
            height=100,
        )
        uploaded_file = None
        if mode == "Document analysis":
            uploaded_file = st.file_uploader(
                label="Upload a synthetic report",
                type=["txt", "md", "pdf", "docx"],
            )
            st.caption("No file? The bundled Markdown example will be used.")

        run_clicked = st.button(label="Run analysis", type="primary", use_container_width=True)

    with right:
        st.subheader("Result")
        if not run_clicked:
            st.info("Choose a role, ask a question, and run the flow.")
            _render_flow_diagram()
            return

        response = _run_flow(
            mode=mode,
            role=contracts.schema.Role(role),
            question=question,
            uploaded_file=uploaded_file,
        )
        _render_response(response=response)


def _run_flow(
    *,
    mode: str,
    role: contracts.schema.Role,
    question: str,
    uploaded_file: UploadedFileLike | None,
) -> contracts.schema.AnswerResponse:
    """Run the selected CareShield pipeline.

    :param mode: UI mode selected by the user.
    :param role: Synthetic caller role.
    :param question: User question.
    :param uploaded_file: Optional Streamlit upload object.
    :return: Structured assistant response.
    """
    assistant = pipeline.assistant.CareShieldAssistant()
    if mode == "Built-in policy Q&A":
        return assistant.ask(
            request=contracts.schema.AskRequest(
                role=role,
                question=question,
            )
        )

    # Keep the UI usable immediately by falling back to the checked-in example.
    content, source_name = _read_upload(uploaded_file=uploaded_file)
    return assistant.analyze_document(
        content=content,
        source_name=source_name,
        role=role,
        question=question,
        sensitivity=contracts.schema.Sensitivity.clinical,
    )


def _read_upload(*, uploaded_file: UploadedFileLike | None) -> tuple[bytes, str]:
    """Read a Streamlit upload or the bundled example.

    :param uploaded_file: Optional Streamlit upload object.
    :return: File bytes and source name.
    """
    if uploaded_file is None:
        return EXAMPLE_PATH.read_bytes(), EXAMPLE_PATH.name

    # Streamlit's UploadedFile exposes getvalue/name at runtime; keeping this
    # small avoids coupling the core app to Streamlit-specific types.
    content = uploaded_file.getvalue()
    source_name = uploaded_file.name
    return content, source_name


def _render_response(*, response: contracts.schema.AnswerResponse) -> None:
    """Render a structured assistant response.

    :param response: Assistant response to render.
    """
    st.markdown(response.answer)
    metrics = st.columns(4)
    metrics[0].metric(label="Confidence", value=response.confidence)
    metrics[1].metric(label="Eval score", value=response.eval.score)
    metrics[2].metric(label="Citations", value=len(response.citations))
    metrics[3].metric(label="Redactions", value=len(response.redactions))

    with st.expander(label="Citations", expanded=True):
        for citation in response.citations:
            st.write(f"**{citation.title}** (`{citation.doc_id}`)")
            st.caption(citation.quote)

    with st.expander(label="Trace and raw JSON"):
        st.code(
            body=json.dumps(obj=response.model_dump(mode="json"), indent=2),
            language="json",
        )


def _render_flow_diagram() -> None:
    """Render the learning flow as text."""
    st.code(
        body=(
            "request -> role context -> policy filter -> retrieval -> redaction\n"
            "-> model gateway -> Pydantic validation -> evals -> trace"
        ),
        language="text",
    )


if __name__ == "__main__":
    main()
