"""Conversa inicial de boas-vindas com mensagem estática de onboarding (sem LLM)."""

from apps.ai_engine.prompts import DISCLAIMER

from ..models import Conversation, Message

WELCOME_CONVERSATION_TITLE = "Bem-vindo"
WELCOME_METADATA_FLAG = "welcome"

WELCOME_MESSAGE = (
    "Olá! Sou o MediClaw, assistente de IA para apoio durante o atendimento.\n\n"
    "Use o chat para registrar dados do paciente e solicitar apoio clínico (hipóteses, condutas, "
    "evidências). Para iniciar um atendimento, abra uma **nova conversa** e descreva o paciente — "
    "por exemplo:\n\n"
    '> "Paciente: João Silva, 45 anos, 1,78 m, 82 kg, nasceu em 10/05/1980, sexo masculino. '
    'Dorme em média 6 horas por noite e caminha 30 minutos diariamente."\n\n'
    "Peso, sono, atividade e refeições são salvos automaticamente quando mencionados. "
    "O nome do paciente aparece na conversa assim que identificado.\n\n"
    f"{DISCLAIMER}"
)


def ensure_welcome_conversation(user) -> Conversation | None:
    """
    Cria uma conversa de boas-vindas para o médico recém-cadastrado.
    Retorna None para usuários ADMIN.
    Idempotente: não cria segunda conversa se já existir.
    """
    if getattr(user, "role", None) == "ADMIN":
        return None

    existing = Conversation.all_objects.filter(
        doctor_id=user.id, title=WELCOME_CONVERSATION_TITLE
    ).first()
    if existing:
        return existing

    conv = Conversation.objects.create(
        doctor_id=user.id,
        title=WELCOME_CONVERSATION_TITLE,
    )
    Message.objects.create(
        conversation=conv,
        role="ASSISTANT",
        content=WELCOME_MESSAGE,
        tokens_used=0,
        blocked_by_guardrail=False,
        metadata={WELCOME_METADATA_FLAG: True},
    )
    return conv
