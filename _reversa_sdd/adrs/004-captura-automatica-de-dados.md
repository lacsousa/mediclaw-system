# ADR-004 — Captura automática de dados do paciente por linguagem natural

**Status:** Aceito 🟢
**Data:** evoluído ao longo do MVP (serviços presentes em `ai_engine/services/`)
**Fonte:** `ai_engine/services/capture_rules.py`, `user_data_capture.py`, `data_extraction_llm.py`, testes `tests/ai_engine/test_user_data_capture.py`.

## Contexto

O médico descreve o paciente em linguagem natural no chat ("Paciente João Silva, 1,75 m, 80 kg, dorme 6h"). Para o apoio clínico ser útil (tendências, IMC, prontidão), esses dados precisam ser **estruturados e persistidos** automaticamente, sem obrigar o médico a preencher formulários.

## Decisão

- Extração **rules-first** com regex (peso, altura, DOB, sexo, sono, atividade, nutrição, nome).
- **LLM opcional** (`DATA_CAPTURE_LLM`) para preencher lacunas que as regex não cobrem — via `merge_extracted`, onde **regras vencem** e o LLM só preenche `None`/gaps.
- Pipeline: gatilho léxico (`message_likely_has_health_data`, ≥8 chars + keywords) → `parse_rules` → (opcional) LLM → `has_actionable_data` → `_ensure_patient` (cria/resolve `Patient` por nome e DOB) → `_persist_health_data` (perfil + logs biométricos).
- Cada conversa gera um `Patient` **tentativo**; ao capturar a DOB, a dedup nome+DOB por médico re-vincula a conversa e deleta o tentativo **se ele não tiver dados** (nunca perde logs).

## Consequências

- Prontuário "se atualiza sozinho" conforme o médico fala; o resumo de saúde alimenta o prompt da IA.
- Dados capturados viram `Message.metadata.data_capture` (o que foi salvo/erros/faltando) e `still_missing` orienta o onboarding.
- **Limitações:** timestamps dos logs só vêm via LLM (senão `timezone.now()`); `patient_created` nunca reporta `True` (bug latente — `_patient_just_created` nunca é definido). 🟡
- Custo controlável: com `DATA_CAPTURE_LLM=false`, o sistema roda só com regex (fallback de privacidade/custo).

## Alternativas consideradas

- Formulário estruturado obrigatório — rejeitado por fricção no fluxo de consulta.
- Extração 100% via LLM — mitigado pelo fallback de regex e pela precedência rules-first.
