"""Documentation chatbot agent with inline citations and no router prefixes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Sequence, Tuple

from agentfield import AIConfig, Agent
from agentfield.logger import log_info

if __package__ in (None, ""):
    current_dir = Path(__file__).resolve().parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))

from chunking import chunk_markdown_text, is_supported_file, read_text
from embedding import embed_query, embed_texts
from schemas import (
    AnswerCritique,
    Citation,
    ContextChunk,
    ContextWindow,
    DocAnswer,
    IngestReport,
    InlineAnswer,
    QueryPlan,
)

app = Agent(
    node_id="documentation-chatbot",
    agentfield_server=os.getenv("AGENTFIELD_SERVER", "http://localhost:8080"),
    ai_config=AIConfig(
        model=os.getenv("AI_MODEL", "openrouter/openai/gpt-oss-120b"),
        temperature=0.2,
    ),
)


# ========================= Ingestion Skill =========================


@app.skill()
async def ingest_folder(
    folder_path: str,
    namespace: str = "documentation",
    glob_pattern: str = "**/*",
    chunk_size: int = 1200,
    chunk_overlap: int = 250,
) -> IngestReport:
    """Chunk + embed every supported file inside ``folder_path``."""

    root = Path(folder_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    files = sorted(p for p in root.glob(glob_pattern) if p.is_file())
    supported_files = [p for p in files if is_supported_file(p)]
    skipped = [p.as_posix() for p in files if not is_supported_file(p)]

    if not supported_files:
        return IngestReport(
            namespace=namespace, file_count=0, chunk_count=0, skipped_files=skipped
        )

    global_memory = app.memory.global_scope

    total_chunks = 0
    for file_path in supported_files:
        relative_path = file_path.relative_to(root).as_posix()
        try:
            text = read_text(file_path)
        except Exception as exc:  # pragma: no cover - defensive
            skipped.append(f"{relative_path} (error: {exc})")
            continue

        doc_chunks = chunk_markdown_text(
            text,
            relative_path=relative_path,
            namespace=namespace,
            chunk_size=chunk_size,
            overlap=chunk_overlap,
        )
        if not doc_chunks:
            continue

        embeddings = embed_texts([chunk.text for chunk in doc_chunks])
        for chunk, embedding in zip(doc_chunks, embeddings):
            vector_key = f"{namespace}|{chunk.chunk_id}"
            metadata = {
                "text": chunk.text,
                "namespace": namespace,
                "relative_path": chunk.relative_path,
                "section": chunk.section,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
            }
            await global_memory.set_vector(
                key=vector_key, embedding=embedding, metadata=metadata
            )
            total_chunks += 1

    log_info(
        f"Ingested {total_chunks} chunks from {len(supported_files)} files into namespace '{namespace}'"
    )

    return IngestReport(
        namespace=namespace,
        file_count=len(supported_files),
        chunk_count=total_chunks,
        skipped_files=skipped,
    )


# ========================= QA Reasoners =========================


def _filter_hits(
    hits: Sequence[Dict],
    *,
    namespace: str,
    min_score: float,
) -> List[Dict]:
    filtered: List[Dict] = []
    for hit in hits:
        metadata = hit.get("metadata", {})
        if metadata.get("namespace") != namespace:
            continue
        if hit.get("score", 0.0) < min_score:
            continue
        filtered.append(hit)
    return filtered


def _alpha_key(index: int) -> str:
    if index < 0:
        raise ValueError("Index must be non-negative")

    letters: List[str] = []
    current = index
    while True:
        current, remainder = divmod(current, 26)
        letters.append(chr(ord("A") + remainder))
        if current == 0:
            break
        current -= 1
    return "".join(reversed(letters))


def _build_context_entries(hits: Sequence[Dict]) -> List[ContextChunk]:
    entries: List[ContextChunk] = []
    for hit in hits:
        metadata = hit.get("metadata", {})
        text = metadata.get("text", "").strip()
        if not text:
            continue
        key = _alpha_key(len(entries))
        citation = Citation(
            key=key,
            relative_path=metadata.get("relative_path", "unknown"),
            start_line=int(metadata.get("start_line", 0)),
            end_line=int(metadata.get("end_line", 0)),
            section=metadata.get("section"),
            preview=text[:200],
            score=float(hit.get("score", 0.0)),
        )
        entries.append(ContextChunk(key=key, text=text, citation=citation))
    return entries


def _context_prompt(entries: Sequence[ContextChunk]) -> str:
    if not entries:
        return "(no context available)"
    blocks: List[str] = []
    for entry in entries:
        citation = entry.citation
        section = f" · {citation.section}" if citation.section else ""
        location = f"{citation.relative_path}:{citation.start_line}-{citation.end_line}{section}"
        blocks.append(f"[{entry.key}] {location}\n{entry.text}")
    return "\n\n".join(blocks)


def _filter_citations_by_keys(
    entries: Sequence[ContextChunk], keys: Sequence[str]
) -> List[Citation]:
    lookup = {entry.key: entry.citation for entry in entries}
    unique_keys: List[str] = []
    for key in keys:
        if key not in lookup:
            continue
        if key in unique_keys:
            continue
        unique_keys.append(key)
    return [lookup[key] for key in unique_keys]


def _ensure_plan(data: Any) -> QueryPlan:
    if isinstance(data, QueryPlan):
        return data
    return QueryPlan.model_validate(data)


def _ensure_window(data: Any) -> ContextWindow:
    if isinstance(data, ContextWindow):
        return data
    return ContextWindow.model_validate(data)


def _merge_lists(base: List[str], additions: List[str]) -> List[str]:
    seen = set()
    merged: List[str] = []
    for value in base + additions:
        value_clean = value.strip()
        if not value_clean:
            continue
        if value_clean.lower() in seen:
            continue
        seen.add(value_clean.lower())
        merged.append(value_clean)
    return merged


@app.reasoner()
async def qa_plan(question: str) -> QueryPlan:
    """Analyze the question and return retrieval instructions."""

    return await app.ai(
        system="You design retrieval plans for documentation search.",
        user=f"""Question: {question}

Return focused search terms (2-4), critical words that must appear,
an answer style (direct, step_by_step, or comparison),
and a refusal condition describing when to say you lack information.""",
        schema=QueryPlan,
    )


@app.reasoner()
async def qa_retrieve(
    question: str,
    namespace: str,
    plan: Dict[str, Any],
    top_k: int = 6,
    min_score: float = 0.35,
) -> ContextWindow:
    """Retrieve the highest-signal snippets for the current plan."""

    plan_obj = _ensure_plan(plan)

    query_embedding = embed_query(" \n".join([question] + plan_obj.search_terms))
    global_memory = app.memory.global_scope
    raw_hits = await global_memory.similarity_search(query_embedding, top_k=top_k * 3)

    filtered_hits = _filter_hits(raw_hits, namespace=namespace, min_score=min_score)
    context_entries = _build_context_entries(filtered_hits[:top_k])
    return ContextWindow(contexts=context_entries)


@app.reasoner()
async def qa_synthesize(
    question: str,
    plan: Dict[str, Any],
    contexts: Dict[str, Any],
) -> InlineAnswer:
    """Generate a markdown answer using the supplied snippets."""

    plan_obj = _ensure_plan(plan)
    context_window = _ensure_window(contexts)

    if not context_window.contexts:
        return InlineAnswer(
            answer=(
                "I could not find any matching documentation yet. "
                f"({plan_obj.refusal_condition})"
            ),
            cited_keys=[],
        )

    context_prompt = _context_prompt(context_window.contexts)
    snippets_json = json.dumps(
        {entry.key: entry.text for entry in context_window.contexts}, indent=2
    )

    return await app.ai(
        system=(
            "You are a precise documentation assistant. Answer ONLY when the info is in the context map. "
            "Always respond using GitHub-flavored Markdown and keep citation keys inline like [A] or [B][D]. "
            "If the context is insufficient, respond with a short markdown note explaining that."
        ),
        user=(
            f"Question: {question}\n"
            f"Answer style: {plan_obj.answer_style}\n"
            f"Critical terms that must appear: {', '.join(plan_obj.must_include) or 'none'}\n"
            "Context map (JSON where each key maps to a snippet):\n"
            f"{snippets_json}\n\n"
            "Readable context with locations:\n"
            f"{context_prompt}\n\n"
            "Respond with a concise markdown answer (<= 6 sentences) keeping the citation keys inline."
        ),
        schema=InlineAnswer,
    )


@app.reasoner()
async def qa_review(
    question: str,
    plan: Dict[str, Any],
    contexts: Dict[str, Any],
    answer: str,
) -> AnswerCritique:
    """Meta-review the draft answer for completeness and grounding."""

    plan_obj = _ensure_plan(plan)
    context_window = _ensure_window(contexts)
    context_prompt = _context_prompt(context_window.contexts)

    return await app.ai(
        system=(
            "You audit documentation answers for completeness and hallucinations. "
            "Be strict: request more context whenever key terms are missing or evidence is weak."
        ),
        user=(
            f"Question: {question}\n"
            f"Plan search terms: {plan_obj.search_terms}\n"
            f"Plan must include: {plan_obj.must_include}\n\n"
            f"Draft answer:\n{answer}\n\n"
            "Context provided:\n"
            f"{context_prompt}\n\n"
            "Decide if the answer is well-supported. "
            "If missing details, list the concrete topics or entities that need more retrieval."
        ),
        schema=AnswerCritique,
    )


async def _run_iteration(
    *,
    question: str,
    namespace: str,
    plan: QueryPlan,
    top_k: int,
    min_score: float,
) -> tuple[ContextWindow, InlineAnswer, AnswerCritique]:
    plan_payload = plan.model_dump()

    context_data = await app.call(
        "documentation-chatbot.qa_retrieve",
        question=question,
        namespace=namespace,
        plan=plan_payload,
        top_k=top_k,
        min_score=min_score,
    )
    context_window = _ensure_window(context_data)

    inline_data = await app.call(
        "documentation-chatbot.qa_synthesize",
        question=question,
        plan=plan_payload,
        contexts=context_window.model_dump(),
    )
    inline_answer = InlineAnswer.model_validate(inline_data)

    critique_data = await app.call(
        "documentation-chatbot.qa_review",
        question=question,
        plan=plan_payload,
        contexts=context_window.model_dump(),
        answer=inline_answer.answer,
    )
    critique = AnswerCritique.model_validate(critique_data)

    return context_window, inline_answer, critique


@app.reasoner()
async def qa_answer(
    question: str,
    namespace: str = "documentation",
    top_k: int = 6,
    min_score: float = 0.35,
) -> DocAnswer:
    """Orchestrate planning → retrieval → synthesis → self-review."""

    plan_data = await app.call("documentation-chatbot.qa_plan", question=question)
    plan = _ensure_plan(plan_data)

    max_attempts = 2
    attempt = 0
    latest_contexts = ContextWindow(contexts=[])
    latest_answer = InlineAnswer(answer="I do not know yet.", cited_keys=[])
    latest_critique = AnswerCritique(
        verdict="insufficient",
        needs_more_context=True,
        missing_topics=[],
        hallucination_risk="low",
        improvements=[],
    )

    while attempt < max_attempts:
        attempt += 1
        latest_contexts, latest_answer, latest_critique = await _run_iteration(
            question=question,
            namespace=namespace,
            plan=plan,
            top_k=top_k,
            min_score=min_score,
        )

        if not latest_critique.needs_more_context:
            break

        if not latest_critique.missing_topics:
            # No guidance on what to fetch—stop to avoid loops.
            break

        plan = plan.model_copy(
            update={
                "search_terms": _merge_lists(
                    plan.search_terms, latest_critique.missing_topics
                ),
                "must_include": _merge_lists(
                    plan.must_include, latest_critique.missing_topics
                ),
            }
        )
        log_info(
            f"[qa_answer] Critique requested more context ({latest_critique.missing_topics}); "
            "expanding search terms and retrying."
        )

    if not latest_contexts.contexts:
        refusal = (
            "I did not find that in the documentation yet. "
            f"(Plan refusal condition: {plan.refusal_condition})"
        )
        return DocAnswer(answer=refusal, citations=[], plan=plan)

    citations = _filter_citations_by_keys(
        latest_contexts.contexts, latest_answer.cited_keys
    )
    if not citations:
        citations = [entry.citation for entry in latest_contexts.contexts]

    return DocAnswer(
        answer=latest_answer.answer.strip(),
        citations=citations,
        plan=plan,
    )


# ========================= Bootstrapping =========================


def _warmup_embeddings() -> None:
    try:
        embed_texts(["doc-chatbot warmup"])
        log_info("FastEmbed model warmed up for documentation chatbot")
    except Exception as exc:  # pragma: no cover - best-effort
        log_info(f"FastEmbed warmup failed: {exc}")


if __name__ == "__main__":
    _warmup_embeddings()

    print("📚 Documentation Chatbot Agent")
    print("🧠 Node ID: documentation-chatbot")
    print(f"🌐 Control Plane: {app.agentfield_server}")
    print("Endpoints:")
    print("  • /skills/ingest_folder → documentation-chatbot.ingest_folder")
    print("  • /reasoners/qa_plan → documentation-chatbot.qa_plan")
    print("  • /reasoners/qa_answer → documentation-chatbot.qa_answer")
    app.run(auto_port=True)
