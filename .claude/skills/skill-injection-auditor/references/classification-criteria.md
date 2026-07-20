# Critérios de Classificação — Skill Injection Auditor

Guia para interpretar os resultados da análise semântica e consolidar o veredicto final.
Leia este arquivo quando precisar justificar ou explicar um veredicto ao usuário.

---

## Como o Veredicto é Determinado

O veredicto final combina dois sinais:

| Fonte | Peso | Descrição |
|-------|------|-----------|
| Análise Heurística | Complementar | Detecta padrões textuais conhecidos |
| Análise Semântica | Principal | Detecta intenção, mesmo sem padrões óbvios |

**Regra de ouro:** se qualquer uma das análises retornar risco CRITICO ou ALTO com confiança ≥ 80%, o veredicto final é **MALICIOSO** independentemente da outra análise.

---

## Tabela de Decisão

```
┌─────────────────────────────┬──────────────────────────────┬─────────────────┐
│ Heurística                  │ Semântica                    │ Veredicto Final │
├─────────────────────────────┼──────────────────────────────┼─────────────────┤
│ Nenhum alerta               │ SEGURO                       │ ✅ SEGURO        │
│ Apenas BAIXO                │ SEGURO                       │ ✅ SEGURO        │
│ MÉDIO (≤2 alertas)          │ SEGURO                       │ ⚠️ SUSPEITO      │
│ ALTO (qualquer)             │ SEGURO                       │ ⚠️ SUSPEITO      │
│ Qualquer                    │ SUSPEITO                     │ ⚠️ SUSPEITO      │
│ ALTO (qualquer)             │ MALICIOSO                    │ 🚨 MALICIOSO     │
│ Nenhum                      │ MALICIOSO (confiança ≥ 70%)  │ 🚨 MALICIOSO     │
│ MÉDIO (≥3 alertas)          │ SUSPEITO                     │ 🚨 MALICIOSO     │
└─────────────────────────────┴──────────────────────────────┴─────────────────┘
```

---

## O que Fazer com Cada Veredicto

### ✅ SEGURO
- A skill pode ser instalada e usada normalmente.
- Mencionar brevemente o que foi verificado para dar confiança ao usuário.
- Se houver alertas de nível BAIXO, mencionar como informativos, não bloqueantes.

### ⚠️ SUSPEITO
Apresentar ao usuário:
1. O que especificamente causou a suspeita (trecho + arquivo)
2. Por que pode ser falso positivo (contexto legítimo)
3. Por que pode ser real (cenário de ataque)
4. Recomendação: **não usar até revisão manual ou contato com o autor**

### 🚨 MALICIOSO
Apresentar ao usuário:
1. O risco específico encontrado (tipo + severidade + trecho)
2. O que poderia acontecer se a skill fosse usada
3. Recomendação clara: **não instalar, não usar, descartar o arquivo**
4. Se veio de uma fonte, sugerir reportar ao canal adequado

---

## Considerações sobre Confiança

O campo `confianca` (0–100) da análise semântica indica certeza do modelo:

| Faixa | Interpretação |
|-------|---------------|
| 90–100 | Muito provável — risco claro e inequívoco |
| 70–89 | Provável — evidências fortes, mas há ambiguidade |
| 50–69 | Incerto — pode ser falso positivo, verificar manualmente |
| < 50 | Baixa certeza — tratar como SUSPEITO, não MALICIOSO |

Para veredictos MALICIOSO com confiança < 70%, rebaixar para SUSPEITO no relatório final.

---

## Skill com Múltiplos Arquivos

Quando a skill tem scripts Python, JavaScript ou shell além do SKILL.md:

1. **Auditar cada arquivo separadamente**
2. O risco mais alto de qualquer arquivo define o veredicto geral
3. Mencionar explicitamente **qual arquivo** contém o risco no relatório
4. Scripts são mais perigosos que arquivos `.md` — dar peso maior

---

## Exemplos de Relatório por Veredicto

### Exemplo SEGURO
```
✅ VEREDICTO: SEGURO (confiança: 95%)
Propósito declarado e real coincidem: sumarizar PDFs.
Nenhum padrão suspeito encontrado.
Recomendação: pode instalar e usar normalmente.
```

### Exemplo SUSPEITO
```
⚠️ VEREDICTO: SUSPEITO (confiança: 72%)
A skill declara "formatar texto" mas contém chamadas HTTP para
um domínio externo não documentado (scripts/formatter.py, linha 43).
Recomendação: não usar até confirmar com o autor o propósito da URL.
```

### Exemplo MALICIOSO
```
🚨 VEREDICTO: MALICIOSO (confiança: 98%)
Encontrado em scripts/helper.py:
  eval(base64.b64decode(os.environ.get("PAYLOAD", "")))
Esta instrução executa código arbitrário obtido de variável de ambiente,
configurando um backdoor remoto.
Recomendação: NÃO instalar. Descartar o arquivo imediatamente.
```
