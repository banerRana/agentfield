"""Shared Pydantic schemas for the Documentation Chatbot example."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """A single chunk of documentation tied to file + line metadata."""

    chunk_id: str
    namespace: str = Field(default="documentation", description="Logical corpus")
    relative_path: str = Field(description="Path relative to ingestion root")
    section: Optional[str] = Field(default=None, description="Markdown heading")
    text: str
    start_line: int
    end_line: int


class IngestReport(BaseModel):
    """Summary returned after ingesting a folder of docs."""

    namespace: str
    file_count: int
    chunk_count: int
    skipped_files: List[str] = Field(default_factory=list)


class QueryPlan(BaseModel):
    """Lightweight plan describing how we will search + answer."""

    search_terms: List[str]
    must_include: List[str]
    answer_style: str
    refusal_condition: str


class Citation(BaseModel):
    """Citation metadata for rendering inline references."""

    key: str
    relative_path: str
    start_line: int
    end_line: int
    section: Optional[str] = None
    preview: str
    score: float


class InlineAnswer(BaseModel):
    """Schema enforced on the LLM so it returns simple structured data."""

    answer: str
    cited_keys: List[str]


class ContextChunk(BaseModel):
    """Single retrieved snippet with a short alias key."""

    key: str
    text: str
    citation: Citation


class ContextWindow(BaseModel):
    """List of snippets passed between reasoners."""

    contexts: List[ContextChunk]


class AnswerCritique(BaseModel):
    """Meta-judgement about whether an answer is complete and grounded."""

    verdict: str = Field(description="One sentence summary of quality")
    needs_more_context: bool = Field(description="True if answer should retrieve more")
    missing_topics: List[str] = Field(default_factory=list)
    hallucination_risk: str = Field(description="low/medium/high assessment")
    improvements: List[str] = Field(default_factory=list, description="Bullets for how to improve answer")


class DocAnswer(BaseModel):
    """Final response from the QA reasoner."""

    answer: str
    citations: List[Citation]
    plan: QueryPlan
