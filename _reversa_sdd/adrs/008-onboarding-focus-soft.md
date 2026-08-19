# ADR-008 — Onboarding em dois modos (focus/soft) baseado na prontidão do perfil

**Status:** Aceito 🟢
**Data:** MVP (templates e lógica presentes em `ai_engine/`)
**Fonte:** `ai_engine/skills/user_readiness.py`, `orchestrator.py:158-179`, `prompts.py` (`ONBOARDING_FOCUS_TEMPLATE`, `ONBOARDING_SOFT_APPENDIX`, `ONBOARDING_STILL_MISSING_APPENDIX`), `ai_engine/services/capture_rules.py`.

## Contexto

Um paciente novo frequentemente chega ao chat sem perfil completo (nome, DOB, sexo, altura, peso). Responder perguntas clínicas sem contexto básico é **inseguro** (a IA pode assumir dados que não existem). Mas bloquear todas as respostas até o perfil estar completo criaria fricção.

## Decisão

- **Prontidão derivada** (`UserReadiness.is_complete`): perfil "pronto" = `first_name` + `birth_date` + `biological_sex` + `height_cm` + ≥1 `WeightLog`. Calculada a cada request (não persistida).
- **Três modos de resposta:**
  - **Normal** — perfil completo: prompt padrão com resumo de saúde + RAG.
  - **Focus** — perfil incompleto **e primeira mensagem**: a IA **não responde** perguntas clínicas; só orienta o registro dos dados faltantes (uma ou duas solicitações por vez).
  - **Soft** — perfil incompleto em mensagens seguintes: a IA responde normalmente e inclui um lembrete curto dos dados pendentes.
- Urgência (guardrail) **sobrepõe** o onboarding: sintomas de urgência disparam alerta de emergência antes de qualquer orientação de registro.
- Os itens faltantes (`missing_basics`) são expostos em `Message.metadata` para o frontend orientar o médico.

## Consequências

- Segurança clínica: respostas contextualizadas exigem perfil mínimo; onboarding é não-bloqueante nas mensagens seguintes.
- A captura automática (ADR-004) alimenta o perfil em linguagem natural, então o onboarding tende a se auto-resolver durante o atendimento.
- `still_missing` é reavaliado após cada persistência — o frontend atualiza em tempo real.

## Alternativas consideradas

- Bloquear o chat até o perfil completo — rejeitado (fricção).
- Responder sempre sem checagem de prontidão — rejeitado (risco clínico).
