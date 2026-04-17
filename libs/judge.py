from __future__ import annotations

import json
import os
import openai
import asyncio
from agents import Agent, ModelSettings, function_tool, Runner
from typing import List, Literal, Tuple, Union, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import nest_asyncio
import random

nest_asyncio.apply()

api_key = os.getenv("OPEN_AI_KEY")
openai.api_key = api_key

# ============================================================
# Metadata kept OUTSIDE the judge output
# ============================================================

class JudgmentMetadata(BaseModel):
    experiment_id: str = Field(
        description="Identifier for the evaluation campaign or experiment run."
    )
    item_id: str = Field(
        description="Identifier for the evaluated item or prompt."
    )
    language: str = Field(
        description="Language targeted by the generated lessons."
    )
    topic: str = Field(
        description="Grammar topic addressed by the lessons."
    )
    ablation_a: str = Field(
        description="Label describing the generation condition for the original Lesson A."
    )
    ablation_b: str = Field(
        description="Label describing the generation condition for the original Lesson B."
    )
    prompt_version: Optional[str] = Field(
        default=None,
        description="Optional identifier for the generation prompt version."
    )
    judge_version: Optional[str] = Field(
        default=None,
        description="Optional identifier for the judge prompt/schema version."
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes for this comparison."
    )

    @field_validator(
        "experiment_id",
        "item_id",
        "language",
        "topic",
        "ablation_a",
        "ablation_b",
    )
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Required metadata fields must not be empty.")
        return value


# ============================================================
# Judge output only
# ============================================================

class SingleDocumentJudgment(BaseModel):
    internal_coherence: int = Field(
        ge=0,
        le=4,
        description="0=many internal contradictions, 4=no internal contradictions"
    )
    admission_of_missing_information: int = Field(
        ge=0,
        le=4,
        description="0=no acknowledgment of missing information, 4=strong explicit acknowledgment"
    )
    admission_of_conflicting_information: int = Field(
        ge=0,
        le=4,
        description="0=no acknowledgment of conflicting information, 4=strong explicit acknowledgment"
    )
    usefulness: int = Field(
        ge=0,
        le=4,
        description="0=not useful, 4=highly useful for understanding or teaching the topic"
    )
    assertiveness_calibration: int = Field(
        ge=0,
        le=4,
        description="0=strongly miscalibrated, 4=very well calibrated"
    )
    salient_points: list[str] = Field(
        min_length=1,
        description="Short concrete points supporting the judgment."
    )
    summary: str = Field(
        description="Short justification of the judgment."
    )

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("summary must not be empty")
        if len(value) > 600:
            raise ValueError("summary is too long")
        return value

    @field_validator("salient_points")
    @classmethod
    def validate_salient_points(cls, values: list[str]) -> list[str]:
        cleaned = [v.strip() for v in values if v.strip()]
        if not cleaned:
            raise ValueError("salient_points must contain at least one non-empty item")
        if len(cleaned) > 8:
            raise ValueError("salient_points should stay short; max 8 items")
        return cleaned


class PairwiseDocumentJudgment(BaseModel):
    compatibility: int = Field(
        ge=0,
        le=4,
        description="0=the two documents deeply contradict each others, 4=the two documents are fully compatible"
    )
    detail: int = Field(
        ge=0,
        le=4,
        description="0=B much more detailed, 2=equally detailed, 4=A much more detailed"
    )
    comparative_usefulness: int = Field(
        ge=0,
        le=4,
        description="0=B much more useful, 2=equally useful, 4=A much more useful"
    )
    comparative_admission_of_missing_information: int = Field(
        ge=0,
        le=4,
        description="0=B much better acknowledges missing information, 2=equal, 4=A much better"
    )
    comparative_admission_of_conflicting_information: int = Field(
        ge=0,
        le=4,
        description="0=B much better acknowledges conflicting information, 2=equal, 4=A much better"
    )
    comparative_assertiveness_calibration: int = Field(
        ge=0,
        le=4,
        description="0=B much better calibrated, 2=equal, 4=A much better calibrated"
    )
    preferred_document: Literal["A", "B", "tie"] = Field(
        description="Overall preferred document among the presented Lesson A and Lesson B."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the comparative judgment."
    )
    salient_points: list[str] = Field(
        min_length=1,
        description="Short concrete points supporting the comparative judgment."
    )
    summary: str = Field(
        description="Short justification of the comparative judgment."
    )

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("summary must not be empty")
        if len(value) > 600:
            raise ValueError("summary is too long")
        return value

    @field_validator("salient_points")
    @classmethod
    def validate_salient_points(cls, values: list[str]) -> list[str]:
        cleaned = [v.strip() for v in values if v.strip()]
        if not cleaned:
            raise ValueError("salient_points must contain at least one non-empty item")
        if len(cleaned) > 10:
            raise ValueError("salient_points should stay short; max 10 items")
        return cleaned


class Judgment(BaseModel):
    judgment_A: SingleDocumentJudgment
    judgment_B: SingleDocumentJudgment
    pairwise_judgment: PairwiseDocumentJudgment


# ============================================================
# Wrapper result for your own pipeline
# ============================================================

class JudgeRunResult(BaseModel):
    metadata: JudgmentMetadata
    swapped: bool = Field(
        description="True if the original A/B order was swapped before sending to the judge."
    )
    judgment: Judgment


# ============================================================
# Input models for calling the judge
# ============================================================

class DocumentPairInput(BaseModel):
    metadata: JudgmentMetadata
    lesson_a: str = Field(description="Original Lesson A text before any swap.")
    lesson_b: str = Field(description="Original Lesson B text before any swap.")
    source_summary: Optional[str] = Field(
        default=None,
        description="Optional source context or evidence summary."
    )

    @field_validator("lesson_a", "lesson_b")
    @classmethod
    def validate_lessons(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Lesson text must not be empty.")
        return value


# ============================================================
# Agent definition
# ============================================================

judge = Agent(
    name="Judge",
    model="gpt-5",
    instructions="""
You are a strict evaluator of two grammar lessons labelled Lesson A and Lesson B.

Your task is NOT to determine factual truth.
Do NOT use outside knowledge.
Do NOT infer facts beyond what is written in the two lessons and optional source context.

Return a Judgment object with:
- an individual judgment for Lesson A
- an individual judgment for Lesson B
- a pairwise comparative judgment

Scoring principles for each single-document judgment:
- internal_coherence:
  evaluate whether the lesson is self-consistent and free of contradiction.
- admission_of_missing_information:
  evaluate how explicitly the lesson acknowledges missing or insufficient information.
- admission_of_conflicting_information:
  evaluate how explicitly the lesson acknowledges conflicting information or alternative analyses.
- usefulness:
  evaluate usefulness for understanding or teaching the topic.
- assertiveness_calibration:
  evaluate whether the lesson avoids fake certainty and avoids excessive vagueness.

Scoring principles for the pairwise comparative judgment:
- compatibility:
  evaluate whether the information given in the two lessons are mutually compatible or contradictory.
- detail:
  compare meaningful detail, not mere length.
- comparative_usefulness:
  compare practical usefulness.
- comparative_admission_of_missing_information:
  compare how well each lesson acknowledges missing information.
- comparative_admission_of_conflicting_information:
  compare how well each lesson acknowledges conflicting information.
- comparative_assertiveness_calibration:
  compare how well each lesson calibrates certainty and caution.
- preferred_document:
  choose A, B, or tie.

Important constraints:
- Do not reward verbosity unless it adds meaningful content.
- Prefer tie when neither lesson is clearly better overall.
- Keep summaries short and concrete.
- salient_points must be short, specific, and grounded in the lesson texts.
- The optional source context is only background context; you still must not judge truthfulness.
- Output only a valid Judgment object.
""",
    output_type=Judgment,
)


# ============================================================
# Prompt builder
# ============================================================

def build_judge_input(
    *,
    metadata: JudgmentMetadata,
    presented_lesson_a: str,
    presented_lesson_b: str,
    source_summary: str | None = None,
) -> str:
    parts = [
        "You are given two grammar lessons labelled Lesson A and Lesson B.",
        "Judge them according to the rubric in your instructions.",
        "Do not judge factual truth.",
        "Do not use outside knowledge.",
        "",
        "METADATA:",
        f"- experiment_id: {metadata.experiment_id}",
        f"- item_id: {metadata.item_id}",
        f"- language: {metadata.language}",
        f"- topic: {metadata.topic}",
        f"- original_ablation_a: {metadata.ablation_a}",
        f"- original_ablation_b: {metadata.ablation_b}",
    ]

    if metadata.prompt_version:
        parts.append(f"- prompt_version: {metadata.prompt_version}")
    if metadata.judge_version:
        parts.append(f"- judge_version: {metadata.judge_version}")
    if metadata.notes:
        parts.append(f"- notes: {metadata.notes}")

    if source_summary:
        parts.extend(["", "OPTIONAL SOURCE CONTEXT:", source_summary])

    parts.extend([
        "",
        "LESSON A:",
        presented_lesson_a,
        "",
        "LESSON B:",
        presented_lesson_b,
    ])

    return "\n".join(parts)


# ============================================================
# Swap / unswap utilities
# ============================================================

def maybe_swap_lessons(
    lesson_a: str,
    lesson_b: str,
    rng: random.Random | None = None,
) -> tuple[str, str, bool]:
    """
    Randomly swap A and B before sending to the judge.
    Returns (presented_lesson_a, presented_lesson_b, swapped).
    """
    rng = rng or random.Random()
    swapped = rng.random() < 0.5
    if swapped:
        return lesson_b, lesson_a, True
    return lesson_a, lesson_b, False


def invert_centered_0_to_4(score: int) -> int:
    """
    Invert a centered comparative 0..4 scale around 2.
    0 <-> 4
    1 <-> 3
    2 -> 2
    """
    if score < 0 or score > 4:
        raise ValueError(f"Score out of range for inversion: {score}")
    return 4 - score


def unswap_preferred_document(label: Literal["A", "B", "tie"]) -> Literal["A", "B", "tie"]:
    if label == "A":
        return "B"
    if label == "B":
        return "A"
    return "tie"


def unswap_judgment(judgment: Judgment, swapped: bool) -> Judgment:
    """
    Convert the judge output back to the original A/B orientation.
    If swapped=False, returns unchanged.
    If swapped=True:
    - judgment_A and judgment_B are exchanged
    - all directional pairwise fields are inverted
    - preferred_document is flipped
    - compatibility and confidence stay unchanged
    - pairwise salient_points and summary stay unchanged because they remain valid
      after relabelling, though they may mention A/B textually if your judge writes that.
      To reduce that risk, tell the judge to avoid quoting labels in prose.
    """
    if not swapped:
        return judgment

    pair = judgment.pairwise_judgment

    unswapped_pair = PairwiseDocumentJudgment(
        compatibility=pair.compatibility,
        detail=invert_centered_0_to_4(pair.detail),
        comparative_usefulness=invert_centered_0_to_4(pair.comparative_usefulness),
        comparative_admission_of_missing_information=invert_centered_0_to_4(
            pair.comparative_admission_of_missing_information
        ),
        comparative_admission_of_conflicting_information=invert_centered_0_to_4(
            pair.comparative_admission_of_conflicting_information
        ),
        comparative_assertiveness_calibration=invert_centered_0_to_4(
            pair.comparative_assertiveness_calibration
        ),
        preferred_document=unswap_preferred_document(pair.preferred_document),
        confidence=pair.confidence,
        salient_points=pair.salient_points,
        summary=pair.summary,
    )

    return Judgment(
        judgment_A=judgment.judgment_B,
        judgment_B=judgment.judgment_A,
        pairwise_judgment=unswapped_pair,
    )

# ============================================================
# Main async entry point
# ============================================================

async def judge_pair(
    document_pair: DocumentPairInput,
    *,
    rng: random.Random | None = None,
) -> JudgeRunResult:
    """
    Run the judge on one document pair with random A/B swap.
    The returned judgment is always re-oriented to the ORIGINAL A/B order.
    """
    presented_a, presented_b, swapped = maybe_swap_lessons(
        document_pair.lesson_a,
        document_pair.lesson_b,
        rng=rng,
    )

    judge_input = build_judge_input(
        metadata=document_pair.metadata,
        presented_lesson_a=presented_a,
        presented_lesson_b=presented_b,
        source_summary=document_pair.source_summary,
    )

    result = await Runner.run(judge, judge_input)
    raw_judgment: Judgment = result.final_output
    final_judgment = unswap_judgment(raw_judgment, swapped=swapped)

    return JudgeRunResult(
        metadata=document_pair.metadata,
        swapped=swapped,
        judgment=final_judgment,
    )

# ============================================================
# SYNCH
# ============================================================


def judge_pair_synch(document_pair: DocumentPairInput) -> JudgeRunResult:
    return asyncio.run(judge_pair(document_pair))

# ============================================================
# USAGE
# ============================================================
# metadata = JudgmentMetadata(
#     experiment_id="abl_negation_v1",
#     item_id="tahitian_negation_003",
#     language="Tahitian",
#     topic="Negation",
#     ablation_a="full_system",
#     ablation_b="no_typological_priors",
#     prompt_version="lesson_prompt_v3",
#     judge_version="judge_v2",
#     notes="pairwise epistemic-quality judgment"
# )
#
# pair = DocumentPairInput(
#     metadata=metadata,
#     lesson_a=lesson_a_text,
#     lesson_b=lesson_b_text,
#     source_summary=optional_source_context,
# )
#
# result = await judge_pair(pair)
#
# print(result.metadata.item_id)
# print(result.swapped)
# print(result.judgment.pairwise_judgment.preferred_document)
# print(result.judgment.pairwise_judgment.summary)

