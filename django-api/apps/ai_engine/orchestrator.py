import json
import os
import time
from dataclasses import dataclass, field
from typing import Iterator

from apps.audit.services.log import record
from apps.common.logging_config import get_logger

from .guardrails import check_input, check_output
from .prompts import (
    CITATION_LINE,
    DATA_CAPTURE_SAVED_APPENDIX,
    DISCLAIMER,
    ONBOARDING_FOCUS_TEMPLATE,
    ONBOARDING_SOFT_APPENDIX,
    ONBOARDING_STILL_MISSING_APPENDIX,
    SYSTEM_PROMPT_TEMPLATE,
)
from .providers import get_provider
from .services.capture_models import CaptureResult
from .services.user_data_capture import capture_from_message
from .skills.health_summary import health_summary
from .skills.user_readiness import UserReadiness, get_user_readiness

logger = get_logger(__name__)
HISTORY_WINDOW = int(os.environ.get("HISTORY_WINDOW", "6"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS_PER_RESPONSE", "800"))


@dataclass
class GenerateResult:
    content: str
    tokens_used: int
    blocked_by_guardrail: bool
    citations: list[dict] = field(default_factory=list)
    onboarding_mode: str | None = None
    missing_basics: dict | None = None
    data_capture: dict | None = None


def _format_missing_list(readiness: UserReadiness) -> str:
    labels = readiness.missing_labels_pt()
    if not labels:
        return "(nenhum)"
    return "\n".join(f"- {label}" for label in labels)


def _format_still_missing(capture: CaptureResult) -> str:
    meta = capture.still_missing
    parts = []
    profile = meta.get("profile") or []
    if profile:
        parts.append(f"perfil: {', '.join(profile)}")
    if meta.get("name"):
        parts.append("nome")
    if meta.get("weight_log"):
        parts.append("peso atual (kg)")
    return ", ".join(parts) if parts else "(nenhum)"


def _append_capture_context(system: str, capture: CaptureResult | None) -> str:
    if not capture:
        return system
    summary = capture.saved_summary_pt()
    if summary:
        system += DATA_CAPTURE_SAVED_APPENDIX.format(saved_summary=summary)
    still = _format_still_missing(capture)
    if still != "(nenhum)":
        system += ONBOARDING_STILL_MISSING_APPENDIX.format(still_missing=still)
    return system


def _onboarding_metadata(readiness: UserReadiness, mode: str) -> tuple[str, dict]:
    return mode, readiness.to_metadata()


def _load_history(conversation_id: int) -> list[dict]:
    from apps.conversations.models import Message

    history_qs = Message.objects.filter(conversation_id=conversation_id).order_by(
        "-created_at"
    )[:HISTORY_WINDOW]
    return list(
        reversed([{"role": m.role.lower(), "content": m.content} for m in history_qs])
    )


def _history_with_query(conversation_id: int, query: str) -> list[dict]:
    """
    Monta o histórico de turnos para o LLM.
    Remove o USER final se já foi persistido (stream/send_message) antes do generate.
    """
    history = _load_history(conversation_id)
    if history and history[-1]["role"] == "user" and history[-1]["content"] == query:
        history = history[:-1]
    return [*history, {"role": "user", "content": query}]


def _build_onboarding_focus_messages(
    conversation_id: int,
    query: str,
    readiness: UserReadiness,
    capture: CaptureResult | None = None,
) -> list[dict]:
    missing_list = _format_missing_list(readiness)
    system = ONBOARDING_FOCUS_TEMPLATE.format(missing_list=missing_list)
    system = _append_capture_context(system, capture)
    return [
        {"role": "system", "content": system},
        *_history_with_query(conversation_id, query),
    ]


def _build_messages(
    patient_id: int | None,
    conversation_id: int,
    query: str,
    readiness: UserReadiness | None = None,
    capture: CaptureResult | None = None,
) -> tuple[list[dict], list[dict], str | None, dict | None]:
    from apps.rag.retriever import search

    chunks = search(
        query,
        k=int(os.environ.get("RAG_TOP_K", "5")),
        min_score=float(os.environ.get("RAG_MIN_SCORE", "0.75")),
    )
    rag_context = (
        "\n\n".join(
            f"- {c['content']} {CITATION_LINE.format(source=c['source'])}"
            for c in chunks
        )
        or "(sem evidências específicas para esta consulta)"
    )
    summary = health_summary(patient_id)
    system = SYSTEM_PROMPT_TEMPLATE.format(
        health_summary=json.dumps(summary, ensure_ascii=False),
        rag_context=rag_context,
    )
    system = _append_capture_context(system, capture)

    onboarding_mode = None
    missing_basics = None
    if readiness and not readiness.is_complete:
        missing_list = _format_missing_list(readiness)
        system += ONBOARDING_SOFT_APPENDIX.format(missing_list=missing_list)
        onboarding_mode, missing_basics = _onboarding_metadata(readiness, "soft")

    messages = [
        {"role": "system", "content": system},
        *_history_with_query(conversation_id, query),
    ]
    citations = [{"source": c["source"], "chunk_id": c.get("chunk_id")} for c in chunks]
    return messages, citations, onboarding_mode, missing_basics


def _resolve_messages(
    patient_id: int | None,
    conversation_id: int,
    query: str,
    is_first_message: bool,
    capture: CaptureResult | None = None,
) -> tuple[list[dict], list[dict], str | None, dict | None]:
    readiness = get_user_readiness(patient_id)
    if readiness.is_complete:
        return _build_messages(
            patient_id, conversation_id, query, readiness=readiness, capture=capture
        )

    if is_first_message:
        messages = _build_onboarding_focus_messages(
            conversation_id, query, readiness, capture=capture
        )
        mode, meta = _onboarding_metadata(readiness, "focus")
        return messages, [], mode, meta

    return _build_messages(
        patient_id, conversation_id, query, readiness=readiness, capture=capture
    )


def generate(
    user_id: int,
    conversation_id: int,
    query: str,
    *,
    is_first_message: bool = False,
) -> GenerateResult:
    started = time.time()
    pre = check_input(query)
    if not pre.allowed:
        logger.info(
            "guardrail_blocked",
            phase="input",
            reason=pre.reason,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        record("GUARDRAIL_BLOCKED", user_id=user_id, metadata={"reason": pre.reason})
        return GenerateResult(pre.canned_reply + "\n\n" + DISCLAIMER, 0, True, [])

    capture_result = capture_from_message(conversation_id, user_id, query)
    capture_meta = (
        capture_result.to_metadata()
        if capture_result.saved or capture_result.errors
        else None
    )

    patient_id = capture_result.patient_id
    messages, citations, onboarding_mode, missing_basics = _resolve_messages(
        patient_id, conversation_id, query, is_first_message, capture=capture_result
    )
    provider = get_provider()
    content, tokens = provider.complete(messages, max_tokens=MAX_TOKENS)

    post = check_output(content)
    if not post.allowed:
        logger.info(
            "guardrail_blocked",
            phase="output",
            reason=post.reason,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        record(
            "GUARDRAIL_BLOCKED",
            user_id=user_id,
            metadata={"reason": "output_" + post.reason},
        )
        return GenerateResult(
            post.canned_reply + "\n\n" + DISCLAIMER,
            tokens,
            True,
            [],
            onboarding_mode=onboarding_mode,
            missing_basics=missing_basics or capture_result.still_missing,
            data_capture=capture_meta,
        )

    if not content.strip().endswith(DISCLAIMER):
        content = content.rstrip() + "\n\n" + DISCLAIMER

    latency_ms = int((time.time() - started) * 1000)
    record(
        "MESSAGE_SENT",
        user_id=user_id,
        metadata={"tokens_used": tokens, "blocked": False, "latency_ms": latency_ms},
    )
    return GenerateResult(
        content,
        tokens,
        False,
        citations,
        onboarding_mode=onboarding_mode,
        missing_basics=missing_basics or capture_result.still_missing,
        data_capture=capture_meta,
    )


def generate_stream(
    user_id: int,
    conversation_id: int,
    query: str,
    *,
    is_first_message: bool = False,
) -> Iterator[dict]:
    pre = check_input(query)
    if not pre.allowed:
        logger.info(
            "guardrail_blocked",
            phase="input",
            reason=pre.reason,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        yield {"type": "token", "content": pre.canned_reply + "\n\n" + DISCLAIMER}
        yield {"type": "done", "tokens_used": 0, "blocked": True}
        return

    capture_result = capture_from_message(conversation_id, user_id, query)
    capture_meta = (
        capture_result.to_metadata()
        if capture_result.saved or capture_result.errors
        else None
    )

    patient_id = capture_result.patient_id
    messages, citations, onboarding_mode, missing_basics = _resolve_messages(
        patient_id, conversation_id, query, is_first_message, capture=capture_result
    )
    for c in citations:
        yield {"type": "citation", **c}

    provider = get_provider()
    full = []
    try:
        for token in provider.stream(messages, max_tokens=MAX_TOKENS):
            full.append(token)
            yield {"type": "token", "content": token}
    except Exception as e:
        yield {"type": "error", "code": "LLM_PROVIDER_ERROR", "message": str(e)}
        return

    text = "".join(full)
    post = check_output(text)
    if not post.allowed:
        logger.info(
            "guardrail_blocked",
            phase="output",
            reason=post.reason,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        yield {
            "type": "token",
            "content": "\n\n[A resposta foi suprimida por política de segurança.]",
        }
        yield {
            "type": "done",
            "tokens_used": 0,
            "blocked": True,
            "onboarding_mode": onboarding_mode,
            "missing_basics": missing_basics or capture_result.still_missing,
            "data_capture": capture_meta,
        }
        return

    done_payload: dict = {
        "type": "done",
        "tokens_used": len(text.split()),
        "blocked": False,
        "onboarding_mode": onboarding_mode,
        "missing_basics": missing_basics or capture_result.still_missing,
        "data_capture": capture_meta,
    }
    if capture_result.patient_id:
        done_payload["patient_id"] = capture_result.patient_id
        done_payload["patient_created"] = capture_result.patient_created
        # Inclui o nome para a sidebar do frontend atualizar sem re-fetch
        try:
            from apps.patients.models import Patient

            p = Patient.objects.get(pk=capture_result.patient_id)
            done_payload["patient_first_name"] = p.first_name
        except Exception:
            pass
    yield done_payload
