---
name: skill-injection-auditor
description: "Audita uma skill indicada pelo usuário e detecta se ela contém prompt injection, instruções maliciosas, manipulação de comportamento, ou qualquer tentativa de subverter as regras do Claude. Use esta skill sempre que o usuário quiser verificar se uma skill é segura, pedir para 'auditar uma skill', 'verificar se tem prompt injection', 'checar se a skill é segura', 'analisar a skill por riscos', 'inspecionar uma skill', ou qualquer combinação de skill + segurança/auditoria/verificação. Também deve ser ativada quando o usuário disser 'essa skill parece suspeita', 'posso confiar nessa skill?', ou 'o que essa skill realmente faz?'."
---

# Skill Injection Auditor

Detecta prompt injection, instruções maliciosas e tentativas de manipulação em arquivos SKILL.md.

---

## Fluxo de Execução

### Passo 1 — Localizar a Skill

```bash
# Buscar pelo nome em todos os diretórios de skills
find /mnt/skills/ -name "SKILL.md" 2>/dev/null | head -30
ls /mnt/skills/user/ /mnt/skills/public/ /mnt/skills/examples/ 2>/dev/null

# Se o usuário enviou como upload:
ls /mnt/user-data/uploads/
```

Se não encontrar, listar opções ao usuário antes de continuar.

### Passo 2 — Ler todos os arquivos da Skill

Ler o SKILL.md **e** todos os arquivos em `scripts/`, `references/`, `assets/`.
Obfuscação em arquivos auxiliares também é sinal de alerta.

```bash
find /mnt/skills/<path>/ -type f | sort
```

### Passo 3 — Análise Heurística (padrões de código)

Executar o script de varredura automática:

```bash
python /mnt/skills/user/skill-injection-auditor/scripts/heuristic_scan.py \
  --path "/mnt/skills/<path>/"
```

> 📖 Para entender os padrões detectados, leia: `references/risk-taxonomy.md`

### Passo 4 — Análise Semântica via API Claude

Executar o script que chama a API para análise de intenção:

```bash
python /mnt/skills/user/skill-injection-auditor/scripts/semantic_analysis.py \
  --path "/mnt/skills/<path>/" \
  --skill-name "<nome>"
```

> 📖 Para entender os critérios de classificação, leia: `references/classification-criteria.md`

### Passo 5 — Apresentar Relatório Consolidado

Os scripts imprimem JSON. Consolidar e exibir ao usuário o relatório final no formato:

```
╔══════════════════════════════════════════════════╗
║         RELATÓRIO DE AUDITORIA DE SKILL          ║
╚══════════════════════════════════════════════════╝

📁 Skill: <nome>
{emoji} VEREDICTO: <SEGURO|SUSPEITO|MALICIOSO>
🎯 Confiança: <0-100>%

PROPÓSITO
  Declarado: ...
  Real/Detectado: ...

ANÁLISE HEURÍSTICA
  🔴 Alto risco: N alertas
  🟡 Médio risco: N alertas
  ...

ANÁLISE SEMÂNTICA
  {riscos detalhados com severidade e trecho}

RECOMENDAÇÃO
  ...
```

---

## Casos Especiais

**Skill não encontrada** → listar todas disponíveis com `ls` e pedir confirmação.

**Skill com múltiplos arquivos** → auditar cada um separadamente; scripts e `.sh` têm prioridade.

**Conteúdo obfuscado (base64, `\x`, unicode escape)** → decodificar antes de auditar; a obfuscação em si já eleva o risco para 🟡 MÉDIO.

**Arquivo `.skill` (zip)** → extrair em `/tmp/` antes de auditar:
```bash
mkdir -p /tmp/skill-audit && unzip -o upload.skill -d /tmp/skill-audit/
```
