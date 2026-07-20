#!/usr/bin/env python3
"""
heuristic_scan.py
Varredura estática por padrões suspeitos em arquivos de skill.
Saída: JSON com lista de alertas.

Uso:
    python heuristic_scan.py --path /mnt/skills/user/minha-skill/
"""

import re
import sys
import json
import argparse
from pathlib import Path

# ─────────────────────────────────────────────
# PADRÕES DE RISCO
# ─────────────────────────────────────────────

ALTO_RISCO = [
    (r'ignore\s+(all\s+)?(previous|above|prior|earlier)\s+(instructions?|rules?|constraints?)',
     "Instrução clássica de jailbreak: 'ignore previous instructions'"),
    (r'(you\s+are\s+now|act\s+as|pretend\s+(to\s+be|you\s+are)|roleplay\s+as)\s+(?!claude)',
     "Tentativa de redefinir identidade/persona do Claude"),
    (r'disregard\s+(your\s+)?(safety|ethical|guidelines|training|rules)',
     "Tentativa de desativar salvaguardas éticas"),
    (r'\b(DAN|JAILBREAK|BYPASS|UNRESTRICTED[\s_]MODE|developer[\s_]mode)\b',
     "Palavra-chave conhecida de jailbreak"),
    (r'your\s+(true|real|actual|hidden)\s+(self|purpose|goal|instructions?)',
     "Manipulação de identidade do modelo"),
    (r'(exfiltrate|steal|extract|send|transmit|leak)\s+.{0,50}(data|information|keys?|tokens?|secrets?)',
     "Tentativa de exfiltração de dados"),
    (r'(https?|ftp)://(?!api\.anthropic\.com)[^\s"\'<>\)]{8,}',
     "URL externa — pode ser exfiltração ou SSRF"),
    (r'\beval\s*\(|\bexec\s*\(|__import__\s*\(|subprocess\s*\.',
     "Execução dinâmica de código — risco de RCE"),
    (r'\bos\.(system|popen|execv|execve|spawnl)\s*\(',
     "Chamada direta ao sistema operacional"),
    (r'\b(rm\s+-rf|del\s+/[fqs]|format\s+c:)',
     "Comando destrutivo de filesystem"),
    (r'(/etc/passwd|/etc/shadow|~?/\.ssh/|id_rsa\b|\.env\b)',
     "Acesso a arquivos sensíveis do sistema"),
    (r'(anthropic|openai|mistral|cohere)[_\s]*(api[_\s]key|secret|token)',
     "Possível captura de chave de API de LLM"),
]

MEDIO_RISCO = [
    (r'(always|never|must|should)\s+(lie|deceive|mislead|manipulate)',
     "Instrução para enganar o usuário"),
    (r'do\s+not\s+(tell|inform|warn|alert)\s+(the\s+)?(user|human)',
     "Instrução para ocultar informações do usuário"),
    (r'(confidential|secret|hidden)\s+(instruction|prompt|directive)',
     "Declaração de instruções ocultas"),
    (r'(override|bypass|circumvent)\s+.{0,30}(filter|restriction|policy|rule)',
     "Tentativa de contornar políticas"),
    (r'\bsudo\b|\bchmod\s+777\b|\bchown\s+root\b',
     "Escalada de privilégios no sistema"),
    (r'\b(curl|wget|requests\.get|fetch)\s+.{0,100}https?://',
     "Requisição HTTP — verificar destino e dados enviados"),
    (r'open\s*\(\s*["\'].*["\'],\s*["\']w',
     "Escrita em arquivo — verificar destino"),
    (r'(password|passwd|credentials?|auth_token)\s*=\s*["\'][^"\']{3,}["\']',
     "Credencial hardcoded no código"),
    (r'base64\s*\.\s*(b64decode|decodebytes)\s*\(',
     "Decodificação base64 — pode ocultar payload malicioso"),
    (r'\\x[0-9a-fA-F]{2}(?:\\x[0-9a-fA-F]{2}){3,}',
     "Sequência de bytes hex — possível obfuscação"),
]

BAIXO_RISCO = [
    (r'\b(admin|root|superuser|privileged)\s+(access|mode|permission)\b',
     "Referência a privilégios elevados"),
    (r'(all\s+)?files?\s+in\s+(/|/root|/home|/etc)\b',
     "Acesso amplo ao filesystem"),
    (r'while\s+True\s*:[\s\S]{0,20}pass\b',
     "Possível loop infinito — risco de DoS"),
    (r'input\s*\(|raw_input\s*\(',
     "Leitura de input arbitrário — risco em contexto de automação"),
    (r'\\u[0-9a-fA-F]{4}(?:\\u[0-9a-fA-F]{4}){3,}',
     "Sequência unicode escapada — possível obfuscação"),
]

# ─────────────────────────────────────────────
# FUNÇÕES
# ─────────────────────────────────────────────

def scan_text(texto: str, patterns: list, nivel: str) -> list:
    alertas = []
    for pattern, descricao in patterns:
        matches = re.findall(pattern, texto, re.IGNORECASE | re.MULTILINE)
        if matches:
            # Normalizar matches (podem ser tuples de grupos)
            clean = []
            for m in matches[:3]:
                if isinstance(m, tuple):
                    clean.append(" ".join(x for x in m if x).strip())
                else:
                    clean.append(str(m).strip())
            alertas.append({
                "nivel": nivel,
                "descricao": descricao,
                "ocorrencias": len(matches),
                "exemplos": clean,
            })
    return alertas


def scan_file(filepath: Path) -> dict:
    try:
        texto = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"arquivo": str(filepath), "erro": str(e), "alertas": []}

    alertas = []
    alertas += scan_text(texto, ALTO_RISCO,  "ALTO")
    alertas += scan_text(texto, MEDIO_RISCO, "MÉDIO")
    alertas += scan_text(texto, BAIXO_RISCO, "BAIXO")

    return {
        "arquivo": str(filepath),
        "tamanho_chars": len(texto),
        "alertas": alertas,
    }


def scan_skill(skill_path: str) -> dict:
    base = Path(skill_path)
    if not base.exists():
        return {"erro": f"Caminho não encontrado: {skill_path}"}

    # Coletar todos os arquivos relevantes
    extensoes = {".md", ".py", ".js", ".sh", ".ts", ".txt", ".yaml", ".yml", ".json"}
    arquivos = [f for f in base.rglob("*") if f.is_file() and f.suffix in extensoes]

    if not arquivos:
        arquivos = list(base.rglob("*"))  # fallback: todos os arquivos

    resultados = []
    total_alto = total_medio = total_baixo = 0

    for arq in sorted(arquivos):
        r = scan_file(arq)
        for a in r.get("alertas", []):
            if a["nivel"] == "ALTO":
                total_alto += 1
            elif a["nivel"] == "MÉDIO":
                total_medio += 1
            else:
                total_baixo += 1
        resultados.append(r)

    return {
        "skill_path": str(base),
        "arquivos_escaneados": len(resultados),
        "resumo": {
            "total_alto": total_alto,
            "total_medio": total_medio,
            "total_baixo": total_baixo,
        },
        "resultados": resultados,
    }


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Heuristic scan for prompt injection in skills")
    parser.add_argument("--path", required=True, help="Caminho para a pasta da skill")
    args = parser.parse_args()

    resultado = scan_skill(args.path)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
