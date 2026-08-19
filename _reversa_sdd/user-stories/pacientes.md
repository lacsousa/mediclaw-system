# User Stories — Pacientes

> Fluxo: gestão de pacientes (listar, detalhar, criar/atualizar/excluir, resolução por nome/DOB).
> Cobertura: módulo `patients`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## US-PAT-01 — Listar pacientes

**Como** médico,
**quero** ver a lista dos meus pacientes,
**para** localizar e abrir um atendimento.

- Critérios de aceite:
  - GET `/api/v1/patients/` → 200 lista de pacientes (anotada com últimos dados). 🟢

## US-PAT-02 — Detalhar paciente

**Como** médico,
**quero** ver o detalhe de um paciente,
**para** revisar seu perfil e histórico.

- Critérios de aceite:
  - GET `/api/v1/patients/<id>/` → 200 paciente.
  - Paciente inexistente ou de outro médico → 404 `NOT_FOUND`. 🟢

## US-PAT-03 — Criar / atualizar / excluir paciente

**Como** médico,
**quero** cadastrar, editar e excluir pacientes,
**para** manter o prontuário atualizado.

- Critérios de aceite:
  - PUT/PATCH `/api/v1/patients/<id>/` → 200 atualizado; payload inválido → 400.
  - DELETE `/api/v1/patients/<id>/` → 204; cascade remove dados de saúde (LGPD).
  - Escopo sempre ao médico logado (dono) → 404 para ids de terceiros. 🟢

## US-PAT-04 — Garantir paciente a partir da conversa

**Como** sistema,
**quero** criar/resolver automaticamente o paciente pelo nome (e DOB) citado no chat,
**para** a captura automática de dados (peso, sono, atividade) ter um destino.

- Critérios de aceite:
  - Nome citado na mensagem → `ensure_or_create_patient` vincula à conversa.
  - DOB informada → `resolve_patient_dob` atualiza a data de nascimento.
  - Falha na resolução → loga (sem quebrar o turno). 🟢

## US-PAT-05 — Privacidade do paciente

**Como** plataforma,
**quero** garantir que pacientes só sejam visíveis ao médico dono,
**para** proteger dados sensíveis de saúde (LGPD).

- Critérios de aceite:
  - Todas as rotas filtram por `doctor`; acesso a id de outro médico → 404 (anti-reconhecimento). 🟢
