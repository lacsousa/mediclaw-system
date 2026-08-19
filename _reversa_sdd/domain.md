# Domínio de Negócio — MediClaw

> Gerado pelo **Detetive** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Artefato transversal — documenta o "porquê" do sistema, extraído do código, do histórico Git e das specs.

---

## 1. Visão geral do domínio

O MediClaw é uma plataforma de **apoio à longevidade e bem-estar preventivo** para **médicos em atendimento**. O médico conversa com um assistente de IA sobre um paciente em consulta, registrando dados biométricos (peso, sono, atividade, nutrição) em linguagem natural. A IA responde com apoio clínico — hipóteses diferenciais, condutas sugeridas e evidências de uma base de conhecimento (RAG) — **nunca** com diagnóstico definitivo ou prescrição.

O domínio tem duas premissas inegociáveis (confirmadas por código e specs):

1. **Escopo clínico restrito:** a IA é apoio à decisão do médico assistente, não fonte de diagnóstico/prescrição. A restrição é aplicada por guardrails (regex de entrada/saída) + prompt + disclaimer obrigatório. 🟢
2. **Dados sensíveis sob LGPD:** dados de saúde são dados pessoais sensíveis (LGPD Art. 11). O cadastro exige consentimento explícito, e a exclusão da conta limpa tudo em cascata. 🟢

O interlocutor do chat é **sempre o médico**; o paciente é descrito pelo médico em terceira pessoa. O sistema infere e persiste os dados do paciente a partir do texto (regex + LLM opcional), mantendo um vínculo paciente↔conversa.

---

## 2. Atores e papéis

| Ator | Descrição | Evidência |
|---|---|---|
| **Médico (USER)** | Papel padrão no cadastro. Dona de pacientes, conversas e logs. Usa o chat para apoio clínico. | `User.role`, `ROLE_CHOICES = [USER, ADMIN]` (accounts/models.py:23) 🟢 |
| **Admin (ADMIN)** | Papel elevado. Cria usuários e vê métricas do dia. Não recebe conversa de boas-vindas. | `IsAdminRole` (common/permissions.py:4), `welcome.py:29` 🟢 |
| **Sistema de IA (MediClaw)** | Orquestra prompts, guardrails, captura de dados e RAG. Não é um ator humano. | `ai_engine/orchestrator.py` 🟢 |

> O **paciente** não é um ator do sistema — é uma entidade descrita pelo médico e representada por `Patient`. Não há login, sessão ou permissão de paciente. 🟢

---

## 3. Glossário

| Termo | Definição | Confiança |
|---|---|---|
| **Prontuário (perfil básico)** | Conjunto mínimo de dados do paciente considerado "pronto" pela IA: `first_name` + `birth_date` + `biological_sex` + `height_cm` + ≥1 `WeightLog`. Fonte da decisão de onboarding. | `user_readiness.py:5,74` 🟢 |
| **Onboarding mode** | Estado derivado da prontidão do perfil. `focus` = primeira mensagem com perfil incompleto (IA só orienta o registro); `soft` = perfil incompleto em mensagens seguintes (IA responde + lembra). | `orchestrator.py:158-179` 🟢 |
| **Captura automática** | Extração e persistência de dados do paciente a partir da mensagem do médico, via regex (rules) e, opcionalmente, LLM. | `ai_engine/services/user_data_capture.py` 🟢 |
| **Guardrail** | Camada de segurança clínica: verifica entrada e saída da IA contra padrões de diagnóstico, prescrição, urgência e texto sem sentido. | `ai_engine/guardrails.py` 🟢 |
| **Knowledge Base / RAG** | Base de documentos científicos indexados em ChromaDB; chunks recuperados contextualizam o prompt com citações. | `apps/rag/` 🟢 |
| **Conversa tentativa vs. paciente deduplicado** | Cada conversa cria um `Patient` próprio ("tentativo") até a DOB ser capturada e a dedup nome+DOB por médico ocorrer. | `patients/services/patient.py` 🟢 |
| **Log biométrico** | Registro imutável (append-only) de peso, sono, atividade ou nutrição de um paciente. | `health_logs/models.py`, views (sem PATCH/PUT) 🟢 |
| **Soft delete** | Conversa "removida" via `deleted_at`; some das listagens mas persiste em `all_objects`. Sem endpoint de restauração. | `conversations/models.py:5-10,30-31` 🟢 |
| **Disclaimer clínico** | Texto fixo: "Conteúdo de apoio à decisão clínica… a avaliação, conduta e responsabilidade são do médico assistente." Anexado a toda resposta com viés clínico. | `ai_engine/prompts.py:57-60` 🟢 |

---

## 4. Regras de domínio

### 4.1 Identidade e acesso (accounts)

| # | Regra | Detalhe | Confiança |
|---|---|---|---|
| R1 | **Login por e-mail** | `USERNAME_FIELD = "email"`; `username` fica em branco e não identifica ninguém. | 🟢 |
| R2 | **E-mail é o identificador único** | `unique=True`, normalizado para minúsculo no cadastro, login e update. | 🟢 |
| R3 | **Política de senha** | Mín. 8 chars com letra e dígito (`^(?=.*[A-Za-z])(?=.*\d).{8,}$`). | 🟢 |
| R4 | **Credenciais sigilosas** | Falha de credencial e usuário inativo retornam o mesmo `INVALID_CREDENTIALS` (401) — não vaza qual o erro. | 🟢 |
| R5 | **Consentimento LGPD obrigatório** | `accept_terms=true` é obrigatório no cadastro; grava `accepted_terms_at = now()`. | 🟢 |
| R6 | **Boas-vindas no cadastro** | Todo usuário `USER` recebe uma conversa "Bem-vindo" estática (idempotente; pulada para `ADMIN`). | 🟢 |
| R7 | **Exclusão de conta** | `DELETE /me` → `user.delete()` → cascata remove pacientes, logs, conversas e mensagens. | 🟢 |

### 4.2 Pacientes e deduplicação (patients)

| # | Regra | Detalhe | Confiança |
|---|---|---|---|
| R8 | **Escopo por médico** | Pacientes só são visíveis/alteráveis pelo médico dono; acesso a outro → `NOT_FOUND` (404). | 🟢 |
| R9 | **Unicidade condicional** | `(doctor, first_name, birth_date)` é único **somente quando** `birth_date` está preenchido (constraint parcial). | 🟢 |
| R10 | **Criação vem do chat** | Não há endpoint POST de paciente; a criação acontece por captura no chat. | 🟢 |
| R11 | **Paciente tentativo por conversa** | Cada conversa gera seu próprio `Patient` até a DOB permitir dedup. | 🟢 |
| R12 | **Merge ao capturar DOB** | Mesmo nome+DOB do médico → re-vincula a conversa ao paciente existente e deleta o tentativo **se ele não tiver nenhum log** (dados nunca são perdidos). | 🟢 |
| R13 | **Nome atualiza o título** | O título da conversa vira o nome do paciente (`[:120]`). | 🟢 |

### 4.3 Logs biométricos (health_logs)

| # | Regra | Detalhe | Confiança |
|---|---|---|---|
| R14 | **Append-only** | Logs não têm PATCH/PUT — histórico biométrico é imutável (só criar/deletar). | 🟢 |
| R15 | **Faixas plausíveis (peso)** | `20 ≤ value_kg ≤ 400`. | 🟢 |
| R16 | **Sem timestamp futuro** | **HTTP:** só `measured_at` (peso) é rejeitado se futuro (`WeightLogSerializer`); `started_at`/`performed_at`/`logged_at` não são validados. **Chat:** todos os 4 tipos rejeitam data futura (`services/persist.py`). | 🟢/🟡 [Revisão Codex] |
| R17 | **Qualidade do sono** | `1 ≤ quality_score ≤ 10`; via chat, default `5`. | 🟢 |
| R18 | **Duração do sono** | `0 < duration_hours ≤ 24` (validação **só** na via chat; REST não valida faixa). | 🟢 |
| R19 | **Janela de resumo** | `window` ∈ {7, 30} dias; valores fora caem para 7. | 🟢 |
| R20 | **Tendência de peso** | `latest_weight (sem janela) − first_weight (na janela)`; `None` se faltar um. 🟡 comportamento assimétrico a validar. | 🟡 |
| R21 | **Validação duplicada** | REST (serializers) e chat (services.persist) validam em paralelo com regras levemente divergentes (R18, nota mínima de nutrição). | 🟢 |

### 4.4 Conversas e mensagens (conversations)

| # | Regra | Detalhe | Confiança |
|---|---|---|---|
| R22 | **Ownership por médico** | Toda consulta de conversa filtra `doctor=request.user`; conversa alheia → `NOT_FOUND`. | 🟢 |
| R23 | **Limite de mensagens** | Máx. 50 mensagens por conversa. **Divergência:** `views.py` hardcoda 50; `chat.py` lê env `MAX_MESSAGES_PER_CONVERSATION`. | 🟢 |
| R24 | **Código de erro do limite** | O erro disparado é `CONVERSATION_FULL` — mas o PROJECT-CONTEXT.md documenta `CONVERSATION_LIMIT_REACHED`. 🔴 especificar qual é o contrato oficial. | 🟡 |
| R25 | **Soft delete** | `DELETE` seta `deleted_at`; sem restauração; sem purga/expurgo. | 🟢 |
| R26 | **Título automático** | Primeira mensagem define o título (`prompt[:80]`) se vazio ou "Nova conversa". | 🟢 |
| R27 | **Turno persistido antes do LLM** | Mensagem USER salva **antes** da chamada; ASSISTANT salva no evento `done` com metadados (citações, onboarding, data_capture). | 🟢 |
| R28 | **Retenção de 90 dias** | `CONVERSATION_RETENTION_DAYS` documentado mas **sem implementação** de job de expurgo. 🔴 LACUNA LGPD. | 🔴 |
| R29 | **Streaming sem throttle** | O caminho principal do frontend (`stream/`) não tem `ChatThrottle`; só `post_message` tem (10/min). | 🟢 |

### 4.5 Camada de IA — guardrails e prompts (ai_engine)

| # | Regra | Detalhe | Confiança |
|---|---|---|---|
| R30 | **Nunca diagnosticar** | Guardrail de entrada bloqueia pedidos de diagnóstico (`qual meu diagnóstico`, `eu estou com câncer`, …). | 🟢 |
| R31 | **Nunca prescrever** | Guardrail bloqueia pedidos de medicamento/dosagem (`prescreva`, `me receite`, `dosagem de`, …). | 🟢 |
| R32 | **Urgência tem prioridade** | Padrões de urgência (dor torácica, falta de ar, desmaio) são checados **primeiro** e orientam encaminhamento imediato (SAMU 192). | 🟢 |
| R33 | **Dupla checagem** | `check_input` antes e `check_output` depois da geração; output bloqueado é suprimido. | 🟢 |
| R34 | **Disclaimer obrigatório** | Toda resposta com viés clínico termina com o `DISCLAIMER` (anexado se ausente). | 🟢 |
| R35 | **Antigibberish** | Entrada sem sentido (sem vogais, repetição `(.)\1{6,}`, <34% palavras plausíveis em textos ≥3 palavras) → bloqueada com mensagem de reformulação. | 🟢 |
| R36 | **Citações RAG** | O modelo só deve embasar afirmações no contexto científico injetado; fonte citada `(fonte: {source})`; sem evidência → responder genericamente sem inventar fontes. | 🟢 |
| R37 | **Provedor LLM configurável** | `LLM_PROVIDER` ∈ {`openai`, `gemini`}. **Divergência de spec:** PROJECT-CONTEXT prevê Anthropic; o código implementa OpenAI e Google Gemini. | 🟡 |
| R38 | **Histórico limitado** | Últimas `HISTORY_WINDOW=6` mensagens entram no prompt. | 🟢 |
| R39 | **Tokens limitados** | `MAX_TOKENS_PER_RESPONSE=800`; streaming conta palavras (`len(text.split())`), não tokens reais. | 🟢 |

### 4.6 Captura automática de dados (ai_engine/services)

| # | Regra | Detalhe | Confiança |
|---|---|---|---|
| R40 | **Ativa por gatilho léxico** | Mensagem só entra no pipeline de captura se tiver ≥8 chars e keyword de saúde (kg, cm, dormi, paciente, anos, …). | 🟢 |
| R41 | **Rules-first, LLM opcional** | Regex têm precedência; LLM (se `DATA_CAPTURE_LLM=true`) só preenche lacunas via `merge_extracted`. | 🟢 |
| R42 | **Dados são persistidos de fato** | Captura cria `WeightLog`/`SleepLog`/`ActivityLog`/`NutritionNote` e atualiza `Patient` (perfil). | 🟢 |
| R43 | **`patient_created` sempre False** | Campo do contrato SSE existe, mas o atributo interno `_patient_just_created` nunca é definido → sempre reporta `False`. Possível bug. | 🟡 |
| R44 | **Datetime não extraído por regex** | Timestamps dos logs só vêm via LLM; sem LLM, usa `timezone.now()`. | 🟢 |
| R45 | **Nota de nutrição** | Capturada via gatilhos (almocei, jantei, comi, refeição…), mínimo 10 chars, truncada a 1000. | 🟢 |

### 4.7 Knowledge Base / RAG (rag)

| # | Regra | Detalhe | Confiança |
|---|---|---|---|
| R46 | **Tipos aceitos** | Só PDF, Markdown e TXT; senão `INVALID_FILE_TYPE`. | 🟢 |
| R47 | **Tamanho máximo** | 10 MB por upload; senão `FILE_TOO_LARGE`. | 🟢 |
| R48 | **Chunking fixo** | `RecursiveCharacterTextSplitter(1000/200)`, hardcoded. | 🟢 |
| R49 | **Ingestão síncrona** | Upload extrai + embeda + grava no Chroma dentro do request — sem fila/background. | 🟢 |
| R50 | **Delete bloqueia PROCESSING** | Documento em processamento não pode ser deletado (409 `CONFLICT`). | 🟢 |
| R51 | **Limiar de relevância** | Score < `min_score` descartado. **Divergência:** função `search()` default `0.40`; orquestrador injeta `RAG_MIN_SCORE=0.75` (env). | 🟡 |
| R52 | **Qualquer autenticado pode alimentar a KB** | Upload/list/status/delete são `IsAuthenticated` (não `IsAdminRole`) — vetor de conteúdo potencialmente inseguro, pois a KB alimenta as respostas do chat. | 🟡 |

### 4.8 Auditoria (audit)

| # | Regra | Detalhe | Confiança |
|---|---|---|---|
| R53 | **Auditoria é stub no MVP** | `record()` é `pass` — eventos (`USER_REGISTERED`, `LOGIN`, `GUARDRAIL_BLOCKED`, `MESSAGE_SENT`, `KB_UPLOAD`, `KB_DELETE`, `ADMIN_CREATED_USER`) são descartados silenciosamente. | 🟢 |
| R54 | **Contrato divergente** | Alguns chamadores usam `user=` (correto) e outros `user_id=` (cai em `**kwargs`). Deve ser padronizado no Epic 3. | 🟢 |
| R55 | **Sem log de conteúdo** | Nenhum evento loga conteúdo de mensagem — só metadados (`conversation_id`, `tokens_used`, `latency_ms`, `reason`). Aderente à política de não logar PII. | 🟢 |

---

## 5. Invariantes críticos (não negociáveis)

| # | Invariante | Aplicação | Confiança |
|---|---|---|---|
| I1 | A IA **nunca** emite diagnóstico definitivo ou prescrição | Guardrails (entrada+saída), system prompt, disclaimer obrigatório | 🟢 |
| I2 | A conversa no chat é **sempre** com o médico; paciente em terceira pessoa | System prompt; guardrails tratam pedidos "em voz de paciente" | 🟢 |
| I3 | Dados de saúde são **sensíveis** (LGPD Art. 11): consentimento no cadastro, minimização, exclusão em cascata | `accepted_terms_at`, `user.delete()` cascata, logs só com metadados | 🟢 |
| I4 | Logs biométricos são **append-only** (histórico não reescreve) | Sem PATCH/PUT nos ViewSets de logs | 🟢 |
| I5 | Ownership rígido por médico em todos os dados de saúde | Querysets filtram `doctor=request.user` | 🟢 |
| I6 | Resposta clínica sempre termina com **disclaimer** | Anexado pelo orquestrador se ausente | 🟢 |

---

## 6. Lacunas (🔴) e inferências (🟡)

### Lacunas — requerem validação humana / implementação

- 🔴 **Retenção LGPD de 90 dias não implementada** (R28): `CONVERSATION_RETENTION_DAYS` documentado, sem job de expurgo. Dados se acumulam indefinidamente (agravado pelo soft-delete sem purga).
- 🔴 **`ActivityLog` de auditoria não existe** (R53): o módulo documentado como "ActivityLog, métricas internas" é um stub. Epic 3 pendente.
- 🔴 **Código de erro de limite indefinido** (R24): `CONVERSATION_FULL` no código vs `CONVERSATION_LIMIT_REACHED` na spec — definir o contrato oficial.
- 🔴 **Provider Anthropic documentado, ausente no código** (R37): spec prevê OpenAI **ou Anthropic**; o código tem OpenAI e Gemini.

### Inferências — plausíveis mas não confirmadas

- 🟡 **Motivo do revert de HttpOnly cookies** (ADR-002): o Git mostra o revert (004e4e2/3ca2a7d) sem mensagem de motivo. Provável trade-off de simplicidade/SSE, mas a razão exata não está documentada.
- 🟡 **Motivo do retorno ao espaço L2 no RAG** (ADR-005): a coleção migrou cosine→L2 (0f193a5) e voltou ao default `space='l2'`. Não há commit explicando o porquê.
- 🟡 **Tendência de peso assimétrica** (R20): `latest` sem janela vs `first` na janela — comportamento provavelmente intencional, a validar com o time de produto.
- 🟡 **`patient_created` sempre False** (R43): possível bug de implementação, não decisão de produto.
