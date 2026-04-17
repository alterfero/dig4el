import json
import asyncio
from typing import Any

import streamlit as st

# Adjust these imports to your project structure
from libs.judge import (
    JudgmentMetadata,
    DocumentPairInput,
    judge_pair
)
from libs import utils

st.set_page_config(page_title="Lesson Judge", layout="wide")

def run_async(coro):
    """
    Safe enough helper for Streamlit to run one async coroutine.
    """
    return asyncio.run(coro)


def load_json_file(uploaded_file) -> dict[str, Any]:
    try:
        return json.load(uploaded_file)
    except Exception as e:
        raise ValueError(f"Invalid JSON file: {e}") from e


def pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


st.title("DIG4EL Lesson Judgment")
st.caption("Compare two lesson outputs with structured LLM-based judgment.")

with st.sidebar:
    st.header("Run settings")
    use_random_seed = st.checkbox("Use deterministic random seed", value=True)
    seed_value = st.number_input("Seed", min_value=0, value=42, step=1)
    show_stringified_lessons = st.checkbox("Show stringified lessons", value=False)
    show_raw_json = st.checkbox("Show raw lesson JSON", value=False)

st.subheader("Metadata")

col1, col2 = st.columns(2)

with col1:
    experiment_id = st.text_input("Experiment ID", value="abl_negation_v1")
    item_id = st.text_input("Item ID", value="item_001")
    language = st.text_input("Language", value="Tahitian")
    topic = st.text_input("Topic", value="Negation")

with col2:
    ablation_a = st.text_input("Ablation A", value="full_system")
    ablation_b = st.text_input("Ablation B", value="no_typological_priors")
    prompt_version = st.text_input("Prompt version", value="lesson_prompt_v3")
    judge_version = st.text_input("Judge version", value="judge_v2")

notes = st.text_area("Notes", value="")

st.subheader("Lesson files")

col_a, col_b = st.columns(2)

with col_a:
    uploaded_a = st.file_uploader("Lesson A JSON", type=["json"], key="lesson_a")

with col_b:
    uploaded_b = st.file_uploader("Lesson B JSON", type=["json"], key="lesson_b")

source_summary = st.text_area(
    "Optional source summary / evidence context",
    value="",
    height=150,
)

run_button = st.button("Run judgment", type="primary", use_container_width=True)

if run_button:
    errors = []

    if uploaded_a is None:
        errors.append("Lesson A JSON is missing.")
    if uploaded_b is None:
        errors.append("Lesson B JSON is missing.")

    if not experiment_id.strip():
        errors.append("Experiment ID is required.")
    if not item_id.strip():
        errors.append("Item ID is required.")
    if not language.strip():
        errors.append("Language is required.")
    if not topic.strip():
        errors.append("Topic is required.")
    if not ablation_a.strip():
        errors.append("Ablation A is required.")
    if not ablation_b.strip():
        errors.append("Ablation B is required.")

    if errors:
        for err in errors:
            st.error(err)
        st.stop()

    try:
        lesson_a_json = load_json_file(uploaded_a)
        lesson_b_json = load_json_file(uploaded_b)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    try:
        lesson_a_text = utils.stringify_lesson(lesson_a_json)
        lesson_b_text = utils.stringify_lesson(lesson_b_json)
    except Exception as e:
        st.error(f"Failed to stringify lessons: {e}")
        st.stop()

    metadata = JudgmentMetadata(
        experiment_id=experiment_id.strip(),
        item_id=item_id.strip(),
        language=language.strip(),
        topic=topic.strip(),
        ablation_a=ablation_a.strip(),
        ablation_b=ablation_b.strip(),
        prompt_version=prompt_version.strip() or None,
        judge_version=judge_version.strip() or None,
        notes=notes.strip() or None,
    )

    pair_input = DocumentPairInput(
        metadata=metadata,
        lesson_a=lesson_a_text,
        lesson_b=lesson_b_text,
        source_summary=source_summary.strip() or None,
    )

    if show_raw_json:
        with st.expander("Raw Lesson A JSON"):
            st.code(pretty_json(lesson_a_json), language="json")
        with st.expander("Raw Lesson B JSON"):
            st.code(pretty_json(lesson_b_json), language="json")

    if show_stringified_lessons:
        with st.expander("Stringified Lesson A"):
            st.text(lesson_a_text)
        with st.expander("Stringified Lesson B"):
            st.text(lesson_b_text)

    with st.spinner("Running judge..."):
        try:
            import random

            rng = random.Random(seed_value) if use_random_seed else None
            result = run_async(judge_pair(pair_input, rng=rng))
        except Exception as e:
            st.exception(e)
            st.stop()

    st.success("Judgment completed.")

    st.subheader("Run info")

    info_col1, info_col2, info_col3 = st.columns(3)
    info_col1.metric("Swapped before judging", "Yes" if result.swapped else "No")
    info_col2.metric("Preferred document", result.judgment.pairwise_judgment.preferred_document)
    info_col3.metric("Confidence", f"{result.judgment.pairwise_judgment.confidence:.2f}")

    st.subheader("Single-document judgments")

    jd_col_a, jd_col_b = st.columns(2)

    with jd_col_a:
        st.markdown("### Lesson A")
        st.write(f"**Internal coherence:** {result.judgment.judgment_A.internal_coherence}/4")
        st.write(f"**Admission of missing information:** {result.judgment.judgment_A.admission_of_missing_information}/4")
        st.write(f"**Admission of conflicting information:** {result.judgment.judgment_A.admission_of_conflicting_information}/4")
        st.write(f"**Usefulness:** {result.judgment.judgment_A.usefulness}/4")
        st.write(f"**Assertiveness calibration:** {result.judgment.judgment_A.assertiveness_calibration}/4")
        st.write("**Salient points:**")
        for p in result.judgment.judgment_A.salient_points:
            st.write(f"- {p}")
        st.write("**Summary:**")
        st.write(result.judgment.judgment_A.summary)

    with jd_col_b:
        st.markdown("### Lesson B")
        st.write(f"**Internal coherence:** {result.judgment.judgment_B.internal_coherence}/4")
        st.write(f"**Admission of missing information:** {result.judgment.judgment_B.admission_of_missing_information}/4")
        st.write(f"**Admission of conflicting information:** {result.judgment.judgment_B.admission_of_conflicting_information}/4")
        st.write(f"**Usefulness:** {result.judgment.judgment_B.usefulness}/4")
        st.write(f"**Assertiveness calibration:** {result.judgment.judgment_B.assertiveness_calibration}/4")
        st.write("**Salient points:**")
        for p in result.judgment.judgment_B.salient_points:
            st.write(f"- {p}")
        st.write("**Summary:**")
        st.write(result.judgment.judgment_B.summary)

    st.subheader("Pairwise judgment")

    pair = result.judgment.pairwise_judgment

    st.write(f"**Compatibility:** {pair.compatibility}/4")
    st.write(f"**Detail:** {pair.detail}/4")
    st.write(f"**Comparative usefulness:** {pair.comparative_usefulness}/4")
    st.write(f"**Comparative admission of missing information:** {pair.comparative_admission_of_missing_information}/4")
    st.write(f"**Comparative admission of conflicting information:** {pair.comparative_admission_of_conflicting_information}/4")
    st.write(f"**Comparative assertiveness calibration:** {pair.comparative_assertiveness_calibration}/4")
    st.write(f"**Preferred document:** {pair.preferred_document}")
    st.write(f"**Confidence:** {pair.confidence:.2f}")

    st.write("**Salient points:**")
    for p in pair.salient_points:
        st.write(f"- {p}")

    st.write("**Summary:**")
    st.write(pair.summary)

    st.subheader("Structured output")

    result_dict = result.model_dump()
    st.json(result_dict)

    st.download_button(
        "Download judgment as JSON",
        data=json.dumps(result_dict, indent=2, ensure_ascii=False),
        file_name=f"{item_id}_judgment.json",
        mime="application/json",
    )