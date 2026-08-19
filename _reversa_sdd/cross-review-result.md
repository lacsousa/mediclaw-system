# Revisão técnica cruzada das specs — MediClaw

Data da revisão: 2026-08-19  
Escopo: units de `accounts`, `patients`, `health_logs`, `conversations`, `ai_engine`, `rag`, `audit/record` e `common`; requisitos/design/tarefas raiz dos módulos; artefatos globais, matrizes de rastreabilidade, OpenAPI e histórias de usuário solicitados.

## Resumo executivo

Foram encontrados **45 apontamentos**:

- **6 inconsistências internas**
- **21 contradições cruzadas**
- **11 lacunas críticas**
- **7 afirmações frágeis marcadas como 🟢 CONFIRMADO**

Os problemas de maior impacto são: vazamento de saída proibida antes do guardrail final no streaming; ausência de validação de ownership nos serviços de paciente; tratamento transversal de erros DRF que produz `UNHANDLED` em vez dos códigos contratados; falta de atomicidade entre banco relacional e ChromaDB; e contrato OpenAPI estruturalmente inválido e materialmente divergente da API.

---

## P-01 — Documento OpenAPI mistura construções incompatíveis com OAS 3.0.3

- **Unit afetada:** global / OpenAPI
- **Arquivo:** `openapi/mediclaw.yaml`
- **Trecho exato:** `openapi: 3.0.3`; `pathItems:`; `type: "null"`
- **Tipo:** Inconsistência interna
- **Severidade:** Alta
- **Problema:** o documento se declara OpenAPI 3.0.3, mas usa `components.pathItems` e o tipo JSON Schema `null`, construções de OpenAPI 3.1. Também há respostas com `oneOf` no nível do Response Object, quando a composição deveria estar no schema de `content`. Validadores 3.0 podem rejeitar o contrato antes mesmo de analisar os endpoints.
- **Sugestão:** escolher uma única versão. Preferencialmente migrar o cabeçalho e toda a sintaxe para 3.1; ou, se 3.0.3 for obrigatório, substituir `type: null` por `nullable: true`, expandir/reorganizar `pathItems` e mover `oneOf` para schemas válidos.

## P-02 — Obrigatoriedade de `patient_id` no GET se contradiz dentro da unit de logs

- **Unit afetada:** `health_logs/crud-viewset`
- **Arquivos:** `requirements.md`, `design.md`
- **Trechos exatos:** “**RN-01** — `patient_id` é obrigatório (query no GET, body no POST); ausente → erro. 🟢”; “**[GET sem patient_id]:** `get_queryset()` retorna `.none()` → lista vazia 200, não erro. 🟢”
- **Tipo:** Inconsistência interna
- **Severidade:** Alta
- **Problema:** requisito normativo e design descrevem respostas diferentes para a mesma requisição. O legado implementa 200 com lista vazia no GET e 400 no POST.
- **Sugestão:** registrar explicitamente a assimetria existente: GET ausente → 200 vazio; POST ausente → 400. Se o comportamento desejado for 400 em ambos, marcá-lo como mudança forward, não como comportamento confirmado.

## P-03 — A unit `stream-sse` descreve uma função e entradas que não existem

- **Unit afetada:** `conversations/stream-sse`
- **Arquivos:** `requirements.md`, `design.md`, `tasks.md`
- **Trechos exatos:** “`conversation_stream(request, conversation_id)`”; “A view recebe a mensagem do usuário via corpo ou query param (a confirmar)”; “Origem no legado: `apps/conversations/views.py:conversation_stream`”
- **Tipo:** Inconsistência interna
- **Severidade:** Alta
- **Problema:** a própria unit se apresenta como especificação executável confirmada, mas usa símbolo inexistente e deixa a entrada principal “a confirmar”. No legado, a função é `stream(request, conv_id)` e `prompt` é query param obrigatório.
- **Sugestão:** substituir a interface pelo símbolo e parâmetros reais; declarar `?token=` e `?prompt=` como entradas obrigatórias e remover a ambiguidade de body/query.

## P-04 — Integração da conversa de boas-vindas tem call site e tolerância a falha incorretos

- **Unit afetada:** `conversations/welcome`
- **Arquivos:** `requirements.md`, `tasks.md`
- **Trechos exatos:** “chamado em `accounts.views.register`”; “Origem no legado: `apps/accounts/views.py`”; “após criar usuário, invoca o serviço; **falha não impede o cadastro**”; “Confiança: 🟢”
- **Tipo:** Inconsistência interna
- **Severidade:** Crítica
- **Problema:** a chamada real ocorre em `RegisterSerializer.create`, não na view, e não está protegida por `try/except`. Uma falha depois de `create_user` pode devolver 500 apesar de o usuário já ter sido gravado.
- **Sugestão:** documentar o call site real e a ausência de isolamento/transação. Tratar “falha não impede cadastro” como requisito futuro ou implementar compensação/on-commit no ciclo forward.

## P-05 — `audit/record` mistura reprodução do MVP com implementação de funcionalidade futura

- **Unit afetada:** `audit/record`
- **Arquivos:** `requirements.md`, `tasks.md`
- **Trechos exatos:** “**RN-02** — Corpo é `pass` — nenhum efeito no MVP. 🟢”; “**T-01**, Implementar `record(...)` persistindo em `ActivityLog`”; “**T-02**, Criar modelo `ActivityLog` com migration”
- **Tipo:** Inconsistência interna
- **Severidade:** Alta
- **Problema:** as tarefas apresentadas como reimplementação do legado mandam criar algo que a própria unit confirma não existir e que foi adiado por ADR. Isso impede saber se “done” significa fidelidade ao legado ou entrega pós-MVP.
- **Sugestão:** separar tarefas em dois planos: baseline fiel (`record` no-op) e evolução pós-MVP (`ActivityLog`), com decisão/ADR e critérios de aceite próprios.

## P-06 — “Toda resposta JSON” com envelope conflita com exceções reconhecidas pela mesma unit

- **Unit afetada:** `common`
- **Arquivo:** `requirements.md`
- **Trechos exatos:** “Toda resposta JSON da API tem forma `{data, error, meta}`”; “Exceções não tratadas pelo DRF fazem o handler retornar `None` → cai no handler 500 padrão do Django. 🟢”
- **Tipo:** Inconsistência interna
- **Severidade:** Média
- **Problema:** erros 500 do Django e eventos SSE não passam necessariamente pelo renderer, logo a universalidade do RF-01 é falsa mesmo segundo RN-03.
- **Sugestão:** restringir o requisito a respostas JSON produzidas pelo DRF e listar explicitamente as exceções: SSE, respostas vazias 204 e handler 500 do Django.

## P-07 — Erros de validação DRF não produzem o código contratado pelas units

- **Units afetadas:** `common`, `accounts`, `patients`, `health_logs`, `conversations`
- **Arquivos:** `common/requirements.md`; requisitos e testes das units consumidoras
- **Trechos exatos:** “payload DRF com chave `code` é usado como `error`; **sem `code`, gera `{code: "UNHANDLED"...}`. 🟢”; “Então recebo 400 `VALIDATION_ERROR`”
- **Tipo:** Contradição cruzada
- **Severidade:** Crítica
- **Problema:** `serializers.ValidationError` normalmente entrega um dict por campo, sem chave superior `code`. O handler documentado o converte para `UNHANDLED`, enquanto dezenas de critérios exigem `VALIDATION_ERROR`.
- **Sugestão:** definir no contrato transversal um mapeamento explícito de `ValidationError` para `VALIDATION_ERROR`, preservando os detalhes por campo; alinhar testes e OpenAPI a esse formato.

## P-08 — Status e códigos de autenticação divergem entre história, OpenAPI e specs de accounts

- **Unit afetada:** `accounts/login`
- **Arquivos:** `user-stories/autenticacao.md`, `openapi/mediclaw.yaml`, `accounts/login/requirements.md`
- **Trechos exatos:** “Credenciais inválidas → 400 `INVALID_CREDENTIALS`”; resposta OpenAPI `"400": ... InvalidCredentials`; “Credenciais incorretas ... → **401** `INVALID_CREDENTIALS`”
- **Tipo:** Contradição cruzada
- **Severidade:** Alta
- **Problema:** o legado e a unit usam 401, enquanto história e contrato público usam 400. Erros padrão do SimpleJWT também podem cair em `UNHANDLED`, não nos códigos `MISSING_TOKEN`/`INVALID_TOKEN` citados em `permissions.md`.
- **Sugestão:** padronizar falha de login em 401 e documentar separadamente autenticação ausente, token inválido e credencial inválida, incluindo o mapeamento real do exception handler.

## P-09 — Contrato de `/me` inventa 204 e omite operações existentes

- **Unit afetada:** `accounts/me`
- **Arquivos:** `user-stories/autenticacao.md`, `openapi/mediclaw.yaml`, `accounts/me/design.md`
- **Trechos exatos:** “Sem `first_name` → 204”; no OpenAPI, `/api/v1/auth/me/` contém somente `get` com resposta `204`; “PATCH ... 200”; “DELETE ... `204 No Content`”
- **Tipo:** Contradição cruzada
- **Severidade:** Alta
- **Problema:** GET sempre retorna o usuário com 200, mesmo com nome vazio. PATCH e DELETE existem no legado/spec da unit, mas não estão expostos no OpenAPI.
- **Sugestão:** remover o 204 do GET e adicionar PATCH/DELETE com schemas e respostas reais.

## P-10 — O mesmo `first_name` aceita regras incompatíveis em três entradas

- **Units afetadas:** `accounts/register`, `accounts/me`, `accounts/persist-user-name`
- **Arquivos:** respectivos `requirements.md`/`design.md`
- **Trechos exatos:** “`name`: obrigatório, max 120”; “`name` ... `allow_blank=True`”; “Tamanho válido: `2 ≤ len ≤ 120`; fora disso → `ValidationError`”
- **Tipo:** Contradição cruzada
- **Severidade:** Alta
- **Problema:** cadastro não define mínimo 2, PATCH permite vazio e o serviço de captura exige pelo menos 2. O domínio não explica por que o mesmo atributo varia conforme o canal.
- **Sugestão:** definir uma regra canônica do nome e, se vazio for permitido para onboarding, documentar estados e transições distintos em vez de validadores acidentais por endpoint.

## P-11 — Payload de criação admin no OpenAPI não corresponde ao serializer

- **Unit afetada:** `accounts/admin-users`
- **Arquivos:** `openapi/mediclaw.yaml`, `accounts/admin-users/requirements.md`
- **Trechos exatos:** OpenAPI: `required: [email, password, first_name]`; unit: “Payload `{email, password, name, role?}`”; “role default `USER`”
- **Tipo:** Contradição cruzada
- **Severidade:** Alta
- **Problema:** cliente gerado pelo OpenAPI enviará `first_name`, mas o serializer exige `name`; o contrato público também omite `role`.
- **Sugestão:** trocar `first_name` por `name`, incluir o enum/default de `role` e usar o schema de saída real do `UserSerializer`.

## P-12 — Histórias e OpenAPI expõem criação/PUT de paciente que não existem

- **Unit afetada:** `patients/detail-crud`
- **Arquivos:** `user-stories/pacientes.md`, `openapi/mediclaw.yaml`, `patients/design.md`
- **Trechos exatos:** “cadastrar e consultar pacientes”; “Editar: PUT `/api/v1/patients/{id}/`”; design da unit: apenas “GET”, “PATCH” e “DELETE” no detalhe
- **Tipo:** Contradição cruzada
- **Severidade:** Alta
- **Problema:** não há POST público de paciente nem PUT no legado; criação ocorre implicitamente via captura do chat.
- **Sugestão:** remover POST/PUT do contrato atual, substituir edição por PATCH e declarar explicitamente que criação direta não é suportada no baseline.

## P-13 — Schema e envelope de pacientes no OpenAPI usam outro modelo de dados

- **Unit afetada:** `patients/list` e `patients/detail-crud`
- **Arquivos:** `openapi/mediclaw.yaml`, `patients/design.md`
- **Trechos exatos:** OpenAPI `Patient`: `doctor_id`, `last_name`, `date_of_birth`, `sex`, `profile`; design: “`{id, first_name, birth_date, biological_sex, height_cm, conversation_count, last_seen_at, latest_weight_kg, created_at, updated_at}`”; listagem: “`{results, count, next}`”
- **Tipo:** Contradição cruzada
- **Severidade:** Crítica
- **Problema:** nomes, cardinalidade e campos derivados são incompatíveis; o OpenAPI modela `data` como array simples, mas a view devolve um objeto de paginação manual dentro do envelope.
- **Sugestão:** reconstruir `Patient` e `PatientListResponse` a partir dos serializers reais e representar `data.results`, `data.count` e `data.next`.

## P-14 — Validações HTTP de sono, atividade, nutrição e datas são atribuídas a serializers que não as fazem

- **Unit afetada:** `health_logs/crud-viewset`
- **Arquivos:** `crud-viewset/design.md`, `health_logs/design.md`, `data-dictionary.md`
- **Trechos exatos:** “Valor fora da faixa: ... sono `0<h≤24`, atividade `duration_min≥1`, nutrição `10–1000` → 400”; “`measured_at`/`started_at`/`performed_at`/`logged_at` futuro → 400”; design raiz: “serializers HTTP **não** validam duração de sono, tamanho mínimo da nota nem timestamps futuros”
- **Tipo:** Contradição cruzada
- **Severidade:** Crítica
- **Problema:** as regras completas existem nos services de captura, não em todos os serializers HTTP. As specs transformam validação dependente do canal em invariante da API.
- **Sugestão:** criar uma matriz campo × entrada (HTTP/chat) e marcar como confirmadas somente as validações realmente compartilhadas.

## P-15 — História pede CRUD completo, enquanto o domínio define logs append-only

- **Unit afetada:** `health_logs`
- **Arquivos:** `user-stories/logs-saude.md`, `health_logs/requirements.md`, `domain.md`
- **Trechos exatos:** “CRUD completo: GET/POST/PUT/PATCH/DELETE”; “Logs são imutáveis: `http_method_names = get/post/delete` (sem PUT/PATCH). 🟢”; “Log biométrico ... imutável (append-only)”
- **Tipo:** Contradição cruzada
- **Severidade:** Alta
- **Problema:** a história e seus critérios exigem edição que o requisito normativo proíbe.
- **Sugestão:** decidir se correção é por exclusão+novo lançamento ou edição auditada; no baseline, remover PUT/PATCH da história e documentar 405.

## P-16 — OpenAPI de health logs usa payload genérico inexistente e omite DELETE de detalhe

- **Unit afetada:** `health_logs/crud-viewset`
- **Arquivos:** `openapi/mediclaw.yaml`, `health_logs/design.md`
- **Trechos exatos:** OpenAPI `HealthLogInput`: `value`, `recorded_at`, `metadata`; design: `value_kg/measured_at`, `duration_hours/started_at`, `type/duration_min/performed_at`, `note/logged_at`; requisito: “DELETE `/api/v1/health/weight/<id>/`”
- **Tipo:** Contradição cruzada
- **Severidade:** Crítica
- **Problema:** nenhum dos quatro serializers aceita o payload genérico publicado, e os paths de exclusão por id não são descritos.
- **Sugestão:** criar quatro schemas de entrada/saída e documentar os quatro endpoints de detalhe DELETE.

## P-17 — Códigos SSE de token na subunit conflitam com o módulo consolidado e o legado

- **Unit afetada:** `conversations/stream-sse`
- **Arquivos:** `stream-sse/requirements.md`, `conversations/requirements.md`
- **Trechos exatos:** “Token ausente/inválido → 401 `MISSING_TOKEN`/`INVALID_TOKEN`”; “ausente/inválido → evento SSE de erro `UNAUTHORIZED` com status 401. 🟢”
- **Tipo:** Contradição cruzada
- **Severidade:** Alta
- **Problema:** a view real usa `UNAUTHORIZED` para ambos. Um cliente não consegue implementar os dois contratos simultaneamente.
- **Sugestão:** manter `UNAUTHORIZED` no baseline ou alterar código e contrato em conjunto; não publicar códigos mais granulares como confirmados.

## P-18 — Wire format SSE documentado não corresponde aos eventos reais

- **Unit afetada:** `conversations/stream-sse`
- **Arquivos:** `stream-sse/requirements.md`, `stream-sse/tasks.md`, `conversations/tasks.md`
- **Trechos exatos:** “Evento `message` com JSON `{content_chunk}`”; “`event: message` + `data: {chunk}`”; módulo raiz: “yield `data: {json}\n\n` por evento (`token`/`citation`/`done`/`error`)”
- **Tipo:** Contradição cruzada
- **Severidade:** Crítica
- **Problema:** o legado não emite linha `event:` nem `{done: true}`; emite JSON discriminado por `type` dentro de linhas `data:`.
- **Sugestão:** especificar ABNF/exemplos exatos para `citation`, `token`, `done` e `error`, todos como `data: <json>\n\n`.

## P-19 — Throttle do stream é simultaneamente confirmado e negado

- **Unit afetada:** `conversations`
- **Arquivos:** `conversations/requirements.md`, `architecture.md`, `domain.md`, `permissions.md`
- **Trechos exatos:** “`ChatThrottle` ... em `post_message` **e `stream`** ... 🟢”; “**Stream sem throttle** ... 🟢”; “só `post_message` tem (10/min). 🟢”
- **Tipo:** Contradição cruzada
- **Severidade:** Crítica
- **Problema:** o caminho de maior custo é descrito com controles opostos. O legado não aplica `ChatThrottle` ao stream.
- **Sugestão:** corrigir o requisito consolidado para “somente REST” e registrar throttle de SSE como lacuna de segurança/custo.

## P-20 — Atomicidade do turno REST contradiz a máquina de estados e a implementação

- **Unit afetada:** `conversations/post-message`
- **Arquivos:** `post-message/requirements.md`, `post-message/design.md`, `state-machines.md`
- **Trechos exatos:** “Persiste ambas as mensagens de forma atômica”; “Persistência atômica (USER + ASSISTANT juntas) ... 🟢”; “Mensagem USER criada em `transaction.atomic` **antes** da chamada LLM (LLM fora da transação) ... 🟢”
- **Tipo:** Contradição cruzada
- **Severidade:** Crítica
- **Problema:** apenas a criação da mensagem USER está na transação; chamada LLM e criação ASSISTANT ficam fora. Falha intermediária deixa turno parcial.
- **Sugestão:** documentar a atomicidade real como “USER isolada em transação” e modelar o estado parcial/retentativa; se atomicidade do par for requisito, redesenhar o fluxo assíncrono/compensatório.

## P-21 — Criação de conversa com título conflita com comportamento fixo do legado

- **Unit afetada:** `conversations/list-create`
- **Arquivos:** `user-stories/chat.md`, `openapi/mediclaw.yaml`, `conversations/list-create/design.md`
- **Trechos exatos:** “POST ... com `{title}`”; OpenAPI: request body `required: true` com `title`; design: “ignora body e cria `title="Nova conversa"`”
- **Tipo:** Contradição cruzada
- **Severidade:** Alta
- **Problema:** clientes são induzidos a enviar um título que será descartado.
- **Sugestão:** remover body/título do baseline público ou implementar o campo como mudança explícita; documentar que o título pode ser substituído pelo primeiro prompt.

## P-22 — Invariante global de disclaimer é falso no streaming

- **Unit afetada:** `ai_engine/generate`
- **Arquivos:** `architecture.md`, `domain.md`, `ai_engine/requirements.md`, `ai_engine/generate/design.md`
- **Trechos exatos:** “garante DISCLAIMER”; “Toda resposta com viés clínico termina com o `DISCLAIMER` ... 🟢”; “no streaming não é anexado programaticamente ... 🟢”; “conformidade LGPD depende do LLM”
- **Tipo:** Contradição cruzada
- **Severidade:** Crítica
- **Problema:** a regra global é válida apenas no REST e em bloqueios de entrada; stream normal não garante o texto.
- **Sugestão:** limitar o invariante ao REST no baseline e criar requisito/teste explícito para anexar o disclaimer antes do evento `done` no stream.

## P-23 — Auditoria de guardrail/mensagem não tem a mesma cobertura no REST e no stream

- **Unit afetada:** `ai_engine/generate`
- **Arquivos:** `ai_engine/requirements.md`, `ai_engine/tasks.md`, `ai_engine/generate/design.md`
- **Trechos exatos:** “Cada evento de bloqueio de guardrail registra `record("GUARDRAIL_BLOCKED")`”; tarefa de stream descreve somente `yield`; rastreabilidade de `record` aponta `orchestrator.py:200,226,245` (fluxo REST)
- **Tipo:** Contradição cruzada
- **Severidade:** Alta
- **Problema:** `generate_stream` loga via logger, mas não chama o stub `record` nos mesmos eventos. Mesmo após implementar auditoria, tráfego SSE ficaria ausente.
- **Sugestão:** especificar cobertura por canal e exigir eventos equivalentes no stream ou declarar explicitamente a assimetria atual.

## P-24 — Endpoint de métricas possui dois caminhos normativos

- **Unit afetada:** `rag` / `audit`
- **Arquivos:** `rag/requirements.md`, `rag/design.md`, `audit/requirements.md`
- **Trechos exatos:** “GET `/api/v1/admin/knowledge/metrics/`”; “o caminho real ... `/api/v1/admin/metrics/`, **não** ... `/knowledge/metrics/` ... 🟢”
- **Tipo:** Contradição cruzada
- **Severidade:** Alta
- **Problema:** o requisito da unit proprietária aponta para uma rota que retorna 404.
- **Sugestão:** adotar `/api/v1/admin/metrics/` no baseline e atualizar requisito, histórias, matriz e links; se a rota for movida, tratar como mudança de compatibilidade.

## P-25 — Casos de uso “administrativos” de KB são autorizados para qualquer usuário

- **Unit afetada:** `rag/upload-ingest`, `rag/delete`, `rag` raiz
- **Arquivos:** `user-stories/gestao-conhecimento.md`, `rag/requirements.md`, `permissions.md`
- **Trechos exatos:** “Como **administrador**”; paths sob `/api/v1/admin/knowledge/`; “Upload/list/status/delete são `IsAuthenticated` (não `IsAdminRole`)”; “Qualquer autenticado pode alimentar a KB”
- **Tipo:** Contradição cruzada
- **Severidade:** Crítica
- **Problema:** papel, namespace e autorização não concordam. Um médico comum pode inserir ou apagar conhecimento global usado nas respostas de todos.
- **Sugestão:** definir ownership/escopo da KB. Para KB global, exigir `IsAdminRole` em upload/list/status/delete e adicionar testes 403; caso contrário, tornar coleção e documentos tenant-scoped.

## P-26 — História de administração diz que cascade não existe, mas specs de dados confirmam exclusão física

- **Unit afetada:** `accounts/me` / global
- **Arquivos:** `user-stories/administracao.md`, `accounts/requirements.md`, `data-dictionary.md`
- **Trechos exatos:** “Retenção 90 dias e cascade delete não implementados”; “DELETE `/api/v1/auth/me/` → 204; dados ... removidos”; “Cadeia LGPD: `User.delete()` → remove `Patient` ... `Conversation` ... `Message`. 🟢”
- **Tipo:** Contradição cruzada
- **Severidade:** Alta
- **Problema:** retenção realmente está ausente, mas cascade está implementado por FKs. A frase agrega uma lacuna real a uma afirmação falsa.
- **Sugestão:** separar os dois itens: manter retenção como lacuna e marcar cascade como comportamento confirmado, incluindo limites relativos a stores externos.

## P-27 — Health check publicado sem envelope conflita com o renderer global

- **Unit afetada:** `common`
- **Arquivos:** `common/requirements.md`, `openapi/mediclaw.yaml`, `common/design.md`
- **Trechos exatos:** “GET `/health/` retorna `{status, db, vector_store, version}`”; “`EnvelopeJSONRenderer` é o `DEFAULT_RENDERER_CLASSES` — toda resposta DRF passa por ele. 🟢”
- **Tipo:** Contradição cruzada
- **Severidade:** Média
- **Problema:** a view usa DRF `Response`; portanto o corpo HTTP normal é envelopado em `data`, salvo override não documentado. OpenAPI e critério de aceite mostram formato raw.
- **Sugestão:** representar `{data: {status,...}, error:null, meta:{}}` no contrato ou configurar/documentar renderer específico para health.

## P-28 — Serviços de paciente não validam que conversa e médico pertencem ao mesmo tenant

- **Unit afetada:** `patients/ensure-or-create`, `patients/resolve-dob`
- **Arquivos:** respectivos `requirements.md` e `design.md`; `permissions.md`
- **Trechos exatos:** “`Conversation.objects.get(pk=conversation_id)`”; “cria `Patient.objects.create(doctor_id=doctor_id, ...)`”; “Ownership rígido ... nunca retorna dados de outro médico”
- **Tipo:** Lacuna crítica
- **Severidade:** Crítica
- **Problema:** o serviço recebe `conversation_id` e `doctor_id` separadamente, mas não exige nem verifica `conv.doctor_id == doctor_id`. Uma chamada incorreta pode vincular paciente de um médico à conversa de outro, atualizar título/relação ou reutilizar paciente estrangeiro.
- **Sugestão:** tornar o owner uma precondição formal e buscar a conversa por `pk` **e** `doctor_id`; adicionar constraint/validação de consistência `conversation.patient.doctor == conversation.doctor` e testes cross-tenant.

## P-29 — Captura pode criar paciente com nome vazio apesar de `first_name` obrigatório

- **Unit afetada:** `patients/ensure-or-create`
- **Arquivos:** `patients/requirements.md`, `ensure-or-create/design.md`
- **Trechos exatos:** “`first_name` é obrigatório”; “cria `Patient.objects.create(..., first_name=first_name.strip())`”
- **Tipo:** Lacuna crítica
- **Severidade:** Alta
- **Problema:** não há precondição nem validação de string vazia no service; `objects.create` não executa `full_clean`, logo `"   "` pode virar `""`.
- **Sugestão:** especificar e validar `1..120` (ou a regra canônica definida em P-10) antes de qualquer escrita e testar whitespace-only.

## P-30 — Deduplicação por nome/DOB não é transacional e não coincide com a constraint

- **Unit afetada:** `patients/resolve-dob`
- **Arquivos:** `requirements.md`, `design.md`
- **Trechos exatos:** “busca ... `first_name__iexact` + `birth_date`”; “constraint parcial `(doctor, first_name, birth_date)`”; “Garante a unicidade ... na prática”
- **Tipo:** Lacuna crítica
- **Severidade:** Crítica
- **Problema:** lookup case-insensitive e constraint case-sensitive não modelam a mesma equivalência. Duas capturas concorrentes também podem passar pela busca e colidir ao salvar, sem `atomic`, lock ou tratamento de `IntegrityError`.
- **Sugestão:** definir normalização canônica/collation, alinhar constraint ao lookup e encapsular resolução em transação com lock/retry determinístico.

## P-31 — Deduplicação não define como mesclar dados do paciente tentativo

- **Unit afetada:** `patients/resolve-dob`
- **Arquivos:** `patients/requirements.md`, `resolve-dob/design.md`
- **Trechos exatos:** “deleta-o apenas se este não tiver logs/refeições”; “se tiver dados, mantém o tentativo existente”
- **Tipo:** Lacuna crítica
- **Severidade:** Alta
- **Problema:** a conversa é religada ao paciente existente, mas logs e perfil do tentativo permanecem em outro registro. O sistema passa a ter dois prontuários para a mesma pessoa sem estratégia de merge, sinalização ou acesso a partir da conversa.
- **Sugestão:** especificar política transacional de merge de logs/perfil, resolução de conflitos e auditoria; até lá, retornar estado explícito `duplicate_requires_merge` em vez de relink silencioso.

## P-32 — Query params numéricos inválidos podem virar 500 sem contrato

- **Unit afetada:** `health_logs/crud-viewset`, `health_logs/summary`
- **Arquivos:** `crud-viewset/design.md`, `summary/requirements.md`, `health_logs/tasks.md`
- **Trechos exatos:** “`patient_id = int(...)`”; “`window = int(query_params.get("window", "7"))`”; somente ausência/faixa de window é especificada
- **Tipo:** Lacuna crítica
- **Severidade:** Alta
- **Problema:** valores como `patient_id=abc` ou `window=abc` levantam `ValueError` não traduzido, potencialmente 500 fora do envelope. Não há critério para zero, negativos ou múltiplos valores.
- **Sugestão:** definir validação por serializer de query e resposta 400 `VALIDATION_ERROR` para formato/domínio inválidos.

## P-33 — Paginação manual não especifica entradas inválidas

- **Unit afetada:** `patients/list`, `conversations/list-create`
- **Arquivos:** respectivos `design.md`/`requirements.md`
- **Trechos exatos:** “`page: int` (default 1)”; “paginação manual, 20 por página”
- **Tipo:** Lacuna crítica
- **Severidade:** Alta
- **Problema:** ambas as views convertem `page` manualmente. Texto, zero ou valor negativo não têm resposta definida e podem gerar `ValueError`/slice inválido em vez de 400 consistente.
- **Sugestão:** especificar `page ≥ 1`, erro padronizado e limites; preferir o paginador comum em vez de lógica duplicada.

## P-34 — Limite de 50 mensagens tem semântica e boundary incorretos

- **Unit afetada:** `conversations/post-message`, `conversations/stream-sse`
- **Arquivos:** `conversations/requirements.md`, `post-message/design.md`, `conversations/tasks.md`
- **Trechos exatos:** “limite de 50 mensagens por conversa”; “se `count >= MAX_MESSAGES` → `CONVERSATION_FULL`”; o turno persiste USER e ASSISTANT
- **Tipo:** Lacuna crítica
- **Severidade:** Alta
- **Problema:** o contador é de linhas `Message`, não de turnos. Com 49 mensagens, o check permite adicionar duas e terminar com 51. REST lê configuração; stream mantém constante própria, abrindo divergência operacional.
- **Sugestão:** definir se o limite é de mensagens ou turnos, reservar capacidade para a resposta (`count + 2 > limit`) e usar uma única configuração compartilhada.

## P-35 — Guardrail de saída no streaming ocorre depois que o conteúdo proibido já foi enviado

- **Unit afetada:** `ai_engine/generate`, `conversations/stream-sse`
- **Arquivos:** `ai_engine/generate/design.md`, `ai_engine/tasks.md`, `state-machines.md`
- **Trechos exatos:** “`provider.stream` → `yield token` por token (acumula `full`)”; depois, “`check_output(text)` bloqueia → `yield token(supressão)`”; “resposta suprimida”
- **Tipo:** Lacuna crítica
- **Severidade:** Crítica
- **Problema:** diagnóstico/prescrição proibidos podem chegar ao cliente token a token antes da avaliação final. Emitir uma mensagem de supressão depois não revoga o conteúdo já recebido; o invariante de guardrail é violado.
- **Sugestão:** aplicar filtro incremental seguro ou bufferizar a saída até validação; no mínimo, não afirmar que o output foi bloqueado/suprimido quando já foi transmitido.

## P-36 — Falha de stream deixa mensagem USER persistida sem estado formal de turno

- **Unit afetada:** `conversations/stream-sse`
- **Arquivos:** `conversations/design.md`, `conversations/tasks.md`
- **Trechos exatos:** “persiste Message USER”; “no `done` persiste Message ASSISTANT”; “exceção ... yield SSE `INTERNAL_ERROR`”
- **Tipo:** Lacuna crítica
- **Severidade:** Alta
- **Problema:** erro do provider, desconexão ou exceção depois da USER deixa mensagem órfã. Não há status `pending/failed`, idempotency key nem regra de retry, podendo duplicar prompts e cobrança.
- **Sugestão:** modelar estado do turno, idempotência e recuperação; registrar falha e permitir retry associado ao mesmo turno.

## P-37 — “Captura nunca quebra o turno” é mais forte que os `except` reais

- **Unit afetada:** `ai_engine/capture`
- **Arquivos:** `requirements.md`, `design.md`
- **Trechos exatos:** “Falhas de persistência são capturadas e logadas; nunca quebram o turno. 🟢”; “Captura silenciosa: exceções por item são acumuladas”
- **Tipo:** Afirmação frágil
- **Severidade:** Crítica
- **Problema:** alguns caminhos capturam somente `ValidationError`; conversões numéricas, `DoesNotExist`, `TypeError` e erros de banco podem escapar. A garantia “nunca” é inferida do propósito, não comprovada por cobertura exaustiva.
- **Sugestão:** rebaixar para 🟡 e listar as classes realmente capturadas; ou criar boundary catch/resultado tipado e testes de falha para cada persistência.

## P-38 — Ingestão e exclusão não têm atomicidade entre PostgreSQL e ChromaDB

- **Unit afetada:** `rag/upload-ingest`, `rag/delete`
- **Arquivos:** `upload-ingest/design.md`, `delete/design.md`
- **Trechos exatos:** “`coll.add(...)` ... depois `doc.status = INDEXED; doc.save()`”; “`get_collection().delete(...)`; `doc.delete()`”
- **Tipo:** Lacuna crítica
- **Severidade:** Crítica
- **Problema:** falha no save após `coll.add` deixa vetores órfãos; falha no delete SQL após apagar Chroma perde rastreabilidade; a ordem inversa produz o problema espelhado. Não há compensação ou reconciliação.
- **Sugestão:** especificar saga/outbox com estados idempotentes, compensação e job de reconciliação por `document_id`; cobrir falhas entre cada etapa.

## P-39 — Usuário inexistente em `persist_user_name` não possui mapeamento válido

- **Unit afetada:** `accounts/persist-user-name`
- **Arquivos:** `requirements.md`, `design.md`, `common/requirements.md`
- **Trechos exatos:** “`User.DoesNotExist` → 404 via handler. 🟡”; “Exceções não tratadas pelo DRF ... handler retorna `None` → ... 500 padrão. 🟢”
- **Tipo:** Lacuna crítica
- **Severidade:** Alta
- **Problema:** `User.DoesNotExist` não é automaticamente transformada em 404 pelo handler descrito. O service pode quebrar a captura com 500, e a própria spec não fixa o contrato.
- **Sugestão:** definir `NOT_FOUND`/resultado nulo no service ou capturar a exceção no orquestrador; não atribuir 404 ao handler sem adaptador explícito.

## P-40 — `user_id` em logs JWT está marcado como confirmado sem considerar a ordem de autenticação

- **Unit afetada:** `common`
- **Arquivos:** `requirements.md`, `design.md`
- **Trechos exatos:** “Enriquecer logs com `user_id` quando autenticado”; “`request_id` e `user_id` bindados em contextvars ... 🟢”
- **Tipo:** Afirmação frágil
- **Severidade:** Alta
- **Problema:** o middleware executa antes da autenticação JWT do DRF, que normalmente ocorre dentro da view. Para requests Bearer, `request.user` pode ainda ser anônimo quando o contexto é bindado. A presença de código de bind não confirma o resultado operacional.
- **Sugestão:** rebaixar para 🟡 até teste de integração com Bearer; mover o bind para ponto posterior à autenticação ou adicionar integração DRF específica.

## P-41 — Rejeição de timestamp futuro está generalizada como invariante confirmado

- **Unit afetada:** `health_logs` / global
- **Arquivos:** `data-dictionary.md`, `erd-complete.md`, `health_logs/crud-viewset/design.md`
- **Trechos exatos:** campos de data descritos com “não pode ser futuro ... 🟢”; “timestamp futuro → 400”
- **Tipo:** Afirmação frágil
- **Severidade:** Alta
- **Problema:** no HTTP, apenas peso possui essa validação completa; sono, atividade e nutrição têm validação mais ampla nos services de chat, não nos serializers correspondentes.
- **Sugestão:** rebaixar a afirmação global para 🟡 e anotar o canal de aplicação; só elevar a 🟢 quando serializer/model/service compartilhado garantir todos os caminhos.

## P-42 — `complete_json` não integra o Protocol confirmado de provider

- **Unit afetada:** `ai_engine/providers`
- **Arquivos:** `requirements.md`, `design.md`
- **Trechos exatos:** “Protocol base: `complete`, `stream`, `complete_json`. 🟢”; tabela de interface atribui `complete_json` a `LLMProvider`
- **Tipo:** Afirmação frágil
- **Severidade:** Média
- **Problema:** o `Protocol` real declara `complete` e `stream`; `complete_json` existe nas implementações concretas, mas não no contrato estrutural base. Tipagem/substituição por provider customizado não garante o método.
- **Sugestão:** rebaixar para 🟡 ou incluir `complete_json` no Protocol e adicionar type-check/teste de conformidade para todos os providers.

## P-43 — “Backend valida MIME” confirmado sugere inspeção de conteúdo que não ocorre

- **Unit afetada:** `rag/upload-ingest`
- **Arquivos:** `rag/requirements.md`, `rag/design.md`, `upload-ingest/design.md`
- **Trechos exatos:** “Upload valida MIME ... no backend ... 🟢”; “MIME confiado no header do cliente (`f.content_type`), sem sniffing ... 🟢”
- **Tipo:** Afirmação frágil
- **Severidade:** Alta
- **Problema:** a checagem é server-side, mas o dado validado é controlado pelo cliente. A afirmação de validação de tipo, sem essa ressalva no requisito, dá uma garantia de segurança indevida.
- **Sugestão:** rebaixar a garantia para 🟡/validação declarativa e exigir sniffing/magic bytes e validação coerente com o parser antes de marcá-la como confirmada.

## P-44 — Conversão L² para “cosine score” depende de hipótese não garantida

- **Unit afetada:** `rag/retrieval`
- **Arquivos:** `rag/design.md`, `retrieval/requirements.md`
- **Trechos exatos:** “Conversão de distância L² → score `max(0.0, 1.0 - dist/2.0)` (**assumindo vetores normalizados OpenAI**) ... 🟢”; “score de similaridade”
- **Tipo:** Afirmação frágil
- **Severidade:** Alta
- **Problema:** a coleção não fixa explicitamente a métrica/caráter normalizado em seu metadata, e a fórmula só equivale a cosseno sob hipóteses específicas. Troca de embedding/configuração altera a semântica do threshold silenciosamente.
- **Sugestão:** rebaixar para 🟡; fixar métrica e normalização na criação da coleção ou usar distância/metadado devolvido pelo store com fórmula documentada e testes de calibração.

## P-45 — Ordenação decrescente por score é marcada como confirmada sem `sort`

- **Unit afetada:** `rag/retrieval`
- **Arquivos:** `retrieval/requirements.md`, `retrieval/design.md`
- **Trechos exatos:** “**RN-06** — Resultado ordenado por score desc. 🟢”; fluxo apenas itera os resultados de `coll.query` e faz filtro por `min_score`
- **Tipo:** Afirmação frágil
- **Severidade:** Média
- **Problema:** o código depende da ordenação retornada pelo ChromaDB e não ordena o resultado após conversão/filtro. Isso é comportamento transitivo do fornecedor, não uma garantia implementada pela unit.
- **Sugestão:** rebaixar para 🟡 ou adicionar `results.sort(key=lambda x: x["score"], reverse=True)` e teste com resposta mock fora de ordem.

---

## Mais graves

1. **P-35:** guardrail pós-hoc no stream permite que conteúdo proibido já seja entregue.
2. **P-28:** services de paciente permitem inconsistência/cross-tenant por falta de verificação de ownership.
3. **P-07:** o handler transversal transforma validações comuns em `UNHANDLED`, invalidando muitos contratos de erro.
4. **P-38:** PostgreSQL e ChromaDB podem divergir permanentemente em ingestão/exclusão.
5. **P-25:** qualquer autenticado pode alterar a base global de conhecimento clínico.
6. **P-19/P-22:** stream principal não tem throttle nem garantia de disclaimer.
7. **P-20/P-36:** turnos REST e SSE podem ficar parcialmente persistidos sem estado de recuperação.
8. **P-01/P-13/P-16/P-18:** o contrato OpenAPI/SSE não é confiável para geração de clientes.
