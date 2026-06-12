from datetime import date

import pytest

from apps.ai_engine.orchestrator import GenerateResult, generate, generate_stream
from apps.ai_engine.prompts import DISCLAIMER
from apps.health_logs.models import WeightLog


@pytest.fixture(autouse=True)
def mock_rag_search(monkeypatch):
    monkeypatch.setattr("apps.rag.retriever.search", lambda *a, **k: [])


class _FakeProvider:
    """Fake LLM provider that returns a configurable response without calling any API."""

    def __init__(self, content="Resposta saudável.", tokens=10):
        self.content = content
        self.tokens = tokens
        self.called = False
        self.last_messages = None

    def complete(self, messages, max_tokens):
        self.called = True
        self.last_messages = messages
        return self.content, self.tokens

    def stream(self, messages, max_tokens):
        self.called = True
        self.last_messages = messages
        for word in self.content.split():
            yield word + " "


class _RaisingProvider:
    """Provider that always raises on any call — used to assert provider is NOT called."""

    def complete(self, messages, max_tokens):
        raise AssertionError("Provider should not have been called")

    def stream(self, messages, max_tokens):
        raise AssertionError("Provider should not have been called")
        return
        yield  # make it a generator


@pytest.mark.django_db
class TestGenerate:
    def _patch_provider(self, monkeypatch, provider):
        monkeypatch.setattr(
            "apps.ai_engine.orchestrator.get_provider", lambda: provider
        )

    def test_orchestrator_blocks_diagnosis_without_calling_llm(self, monkeypatch, user):
        self._patch_provider(monkeypatch, _RaisingProvider())
        result = generate(user.id, conversation_id=0, query="Qual é o meu diagnóstico?")
        assert result.blocked_by_guardrail is True
        assert result.tokens_used == 0

    def test_orchestrator_blocks_urgency_without_calling_llm(self, monkeypatch, user):
        self._patch_provider(monkeypatch, _RaisingProvider())
        result = generate(user.id, conversation_id=0, query="Estou com dor forte no peito")
        assert result.blocked_by_guardrail is True

    def test_orchestrator_blocks_prescription_without_calling_llm(self, monkeypatch, user):
        self._patch_provider(monkeypatch, _RaisingProvider())
        result = generate(user.id, conversation_id=0, query="Que remédio devo tomar?")
        assert result.blocked_by_guardrail is True

    def test_orchestrator_appends_disclaimer(self, monkeypatch, user):
        provider = _FakeProvider(content="Dica sobre exercício.")
        self._patch_provider(monkeypatch, provider)
        result = generate(user.id, conversation_id=0, query="Como me exercitar melhor?")
        assert result.blocked_by_guardrail is False
        assert result.content.endswith(DISCLAIMER)

    def test_orchestrator_does_not_double_append_disclaimer(self, monkeypatch, user):
        provider = _FakeProvider(
            content="Dica sobre sono. " + DISCLAIMER
        )
        self._patch_provider(monkeypatch, provider)
        result = generate(user.id, conversation_id=0, query="Como melhorar o sono?")
        assert result.content.count(DISCLAIMER) == 1

    def test_orchestrator_returns_tokens_used(self, monkeypatch, user):
        provider = _FakeProvider(content="Tudo bem.", tokens=42)
        self._patch_provider(monkeypatch, provider)
        result = generate(user.id, conversation_id=0, query="Qual a importância da hidratação?")
        assert result.tokens_used == 42

    def test_orchestrator_handles_provider_error(self, monkeypatch, user):
        from apps.common.exceptions import LLMProviderError

        def _bad_provider():
            class Bad:
                def complete(self, messages, max_tokens):
                    raise LLMProviderError("timeout")
            return Bad()

        monkeypatch.setattr("apps.ai_engine.orchestrator.get_provider", _bad_provider)
        with pytest.raises(LLMProviderError):
            generate(user.id, conversation_id=0, query="Quantas horas devo dormir?")

    def test_blocked_canned_reply_contains_disclaimer(self, monkeypatch, user):
        self._patch_provider(monkeypatch, _RaisingProvider())
        result = generate(user.id, conversation_id=0, query="Que remédio devo tomar?")
        assert DISCLAIMER in result.content

    def test_output_guardrail_blocks_forbidden_response(self, monkeypatch, user):
        provider = _FakeProvider(content="Você tem câncer, precisará de quimio.")
        self._patch_provider(monkeypatch, provider)
        result = generate(user.id, conversation_id=0, query="O que causa câncer?")
        assert result.blocked_by_guardrail is True

    def test_first_message_incomplete_uses_focus_onboarding(self, monkeypatch, user):
        provider = _FakeProvider()
        self._patch_provider(monkeypatch, provider)

        def _no_rag(*args, **kwargs):
            raise AssertionError("RAG should not be called in focus onboarding")

        monkeypatch.setattr("apps.rag.retriever.search", _no_rag)

        result = generate(
            user.id,
            conversation_id=0,
            query="Como melhorar o sono?",
            is_first_message=True,
        )
        assert result.onboarding_mode == "focus"
        assert result.missing_basics is not None
        assert result.missing_basics["weight_log"] is True
        system = provider.last_messages[0]["content"]
        assert "dados básicos" in system.lower() or "DADOS" in system

    def test_second_message_incomplete_uses_soft_appendix(self, monkeypatch, user):
        provider = _FakeProvider()
        self._patch_provider(monkeypatch, provider)
        monkeypatch.setattr("apps.rag.retriever.search", lambda *a, **k: [])

        generate(
            user.id,
            conversation_id=0,
            query="Como melhorar o sono?",
            is_first_message=False,
        )
        system = provider.last_messages[0]["content"]
        assert "DADOS BÁSICOS DO PACIENTE AINDA PENDENTES" in system

    def test_complete_patient_skips_onboarding(self, monkeypatch, user):
        from apps.conversations.models import Conversation
        from apps.patients.models import Patient

        patient = Patient.objects.create(
            doctor=user,
            first_name="Carlos",
            birth_date=date(1990, 1, 1),
            biological_sex="M",
            height_cm=175,
        )
        WeightLog.objects.create(
            patient=patient, value_kg=80.0, measured_at="2025-01-01T10:00:00Z"
        )
        conv = Conversation.objects.create(doctor=user, patient=patient)

        provider = _FakeProvider()
        self._patch_provider(monkeypatch, provider)
        monkeypatch.setattr("apps.rag.retriever.search", lambda *a, **k: [])

        result = generate(
            user.id,
            conversation_id=conv.id,
            query="Como melhorar o sono?",
            is_first_message=True,
        )
        assert result.onboarding_mode is None
        system = provider.last_messages[0]["content"]
        assert "DADOS BÁSICOS AINDA PENDENTES" not in system
        assert "DADOS BÁSICOS DO PACIENTE AINDA PENDENTES" not in system
        assert "faltam dados básicos do paciente" not in system.lower()

    def test_urgency_on_first_message_skips_onboarding(self, monkeypatch, user):
        self._patch_provider(monkeypatch, _RaisingProvider())
        result = generate(
            user.id,
            conversation_id=0,
            query="Estou com dor forte no peito",
            is_first_message=True,
        )
        assert result.blocked_by_guardrail is True
        assert result.onboarding_mode is None

    def test_capture_injects_saved_summary_in_prompt(self, monkeypatch, user):
        from apps.conversations.models import Conversation

        monkeypatch.setenv("DATA_CAPTURE_LLM", "false")
        provider = _FakeProvider()
        self._patch_provider(monkeypatch, provider)
        monkeypatch.setattr("apps.rag.retriever.search", lambda *a, **k: [])

        conv = Conversation.objects.create(doctor=user, title="Nova conversa")

        result = generate(
            user.id,
            conversation_id=conv.id,
            query="Me chamo João. Peso 80 kg, altura 175 cm, nasci 15/03/1990, sou homem",
            is_first_message=True,
        )
        assert result.data_capture is not None
        assert "weight_log" in result.data_capture.get("saved", {})
        system = provider.last_messages[0]["content"]
        assert "DADOS REGISTRADOS" in system


@pytest.mark.django_db
class TestGenerateStream:
    def _patch_provider(self, monkeypatch, provider):
        monkeypatch.setattr(
            "apps.ai_engine.orchestrator.get_provider", lambda: provider
        )

    def test_stream_blocks_diagnosis_immediately(self, monkeypatch, user):
        self._patch_provider(monkeypatch, _RaisingProvider())
        events = list(generate_stream(user.id, conversation_id=0, query="Qual o meu diagnóstico?"))
        types = [e["type"] for e in events]
        assert "token" in types
        assert "done" in types
        done = next(e for e in events if e["type"] == "done")
        assert done["blocked"] is True

    def test_stream_yields_tokens_for_normal_query(self, monkeypatch, user):
        provider = _FakeProvider(content="Hidratação é essencial.")
        self._patch_provider(monkeypatch, provider)
        events = list(generate_stream(user.id, conversation_id=0, query="Importância da água?"))
        token_events = [e for e in events if e["type"] == "token"]
        assert len(token_events) > 0
        done = next(e for e in events if e["type"] == "done")
        assert done["blocked"] is False

    def test_stream_includes_prior_turns_without_duplicate_user(
        self, monkeypatch, user
    ):
        from apps.conversations.models import Conversation, Message

        conv = Conversation.objects.create(doctor=user, title="Test")
        Message.objects.create(conversation=conv, role="USER", content="Me chamo João")
        Message.objects.create(
            conversation=conv, role="ASSISTANT", content="Olá João!"
        )
        Message.objects.create(
            conversation=conv, role="USER", content="Qual é meu nome?"
        )

        provider = _FakeProvider()
        self._patch_provider(monkeypatch, provider)
        monkeypatch.setattr("apps.rag.retriever.search", lambda *a, **k: [])

        list(
            generate_stream(
                user.id,
                conv.id,
                "Qual é meu nome?",
                is_first_message=False,
            )
        )

        turns = [m for m in provider.last_messages if m["role"] != "system"]
        assert turns == [
            {"role": "user", "content": "Me chamo João"},
            {"role": "assistant", "content": "Olá João!"},
            {"role": "user", "content": "Qual é meu nome?"},
        ]
        assert len([m for m in turns if m["role"] == "user"]) == 2


@pytest.mark.django_db
class TestMultiTurnHistory:
    def _patch_provider(self, monkeypatch, provider):
        monkeypatch.setattr(
            "apps.ai_engine.orchestrator.get_provider", lambda: provider
        )

    def test_generate_includes_prior_turns_without_duplicate_user(
        self, monkeypatch, user
    ):
        from apps.conversations.models import Conversation, Message

        conv = Conversation.objects.create(doctor=user, title="Test")
        Message.objects.create(conversation=conv, role="USER", content="Me chamo João")
        Message.objects.create(
            conversation=conv, role="ASSISTANT", content="Olá João!"
        )
        Message.objects.create(
            conversation=conv, role="USER", content="Qual é meu nome?"
        )

        provider = _FakeProvider()
        self._patch_provider(monkeypatch, provider)
        monkeypatch.setattr("apps.rag.retriever.search", lambda *a, **k: [])

        generate(
            user.id,
            conv.id,
            "Qual é meu nome?",
            is_first_message=False,
        )

        turns = [m for m in provider.last_messages if m["role"] != "system"]
        assert turns == [
            {"role": "user", "content": "Me chamo João"},
            {"role": "assistant", "content": "Olá João!"},
            {"role": "user", "content": "Qual é meu nome?"},
        ]
        for i in range(1, len(turns)):
            assert turns[i]["role"] != turns[i - 1]["role"]
