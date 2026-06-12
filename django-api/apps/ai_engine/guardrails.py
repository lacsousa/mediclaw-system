import re
import unicodedata
from dataclasses import dataclass


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str = ""
    canned_reply: str = ""


# Bloqueia pedidos em voz de paciente (texto colado ou confusão de papel)
DIAGNOSIS_PATTERNS = [
    r"\bqual\s+(é\s+)?(o\s+)?(meu|teu)\s+diagn[oó]stico\b",
    r"\b(eu|estou)\s+com\s+(c[aâ]ncer|infarto|avc|covid)\b",
    r"\bdiagnostique\s+(o\s+que\s+)?(eu\s+)?tenho\b",
    r"\bisso\s+[ée]\s+(uma\s+)?(c[aâ]ncer|tumor|infec[cç][aã]o)\b",
]

PRESCRIPTION_PATTERNS = [
    r"\bque\s+rem[ée]dio\s+(devo\s+)?tomar\b",
    r"\bprescreva\b",
    r"\bme\s+receite\b",
    r"\bdosagem\s+(de|para)\b",
]

URGENCY_PATTERNS = [
    r"\bdor\s+(forte|intensa)\s+no\s+peito\b",
    r"\bfalta\s+de\s+ar\b",
    r"\bdesmai(ei|ar|ou|ando)\b",
    r"\bn[aã]o\s+consigo\s+respirar\b",
]

DIAGNOSIS_REPLY = (
    "Não posso fechar diagnóstico com base nesta solicitação. "
    "Posso ajudar com hipóteses diferenciais e condutas sugeridas quando você descrever o quadro do paciente."
)
PRESCRIPTION_REPLY = (
    "Não posso indicar medicamentos, fármacos ou posologia. "
    "A prescrição é de sua responsabilidade como médico assistente."
)
URGENCY_REPLY = (
    "O quadro descrito pode indicar urgência. Priorize estabilização do paciente e encaminhamento imediato "
    "(SAMU 192 / pronto-socorro), conforme seu julgamento clínico."
)
GIBBERISH_REPLY = (
    "Não entendi a mensagem. Reformule com clareza — por exemplo, uma pergunta clínica sobre o paciente "
    'ou registro em prontuário: "Paciente João Silva, 1,75 m, 80 kg, dorme 6 h/noite".'
)

_SHORT_OK_WORDS = frozenset(
    {
        "ok",
        "oi",
        "ola",
        "olá",
        "sim",
        "nao",
        "não",
        "m",
        "f",
        "kg",
        "cm",
        "h",
        "min",
    }
)
_VOWELS = frozenset("aeiouáàâãéêíóôõúü")

FORBIDDEN_OUTPUT_PATTERNS = [
    r"\bvoc[eê]\s+tem\s+(c[aâ]ncer|infarto|avc|diabetes\s+tipo\s+2)\b",
    r"\bo\s+paciente\s+tem\s+(c[aâ]ncer|infarto|avc|diabetes\s+tipo\s+2)\b",
    r"\bdiagn[oó]stico\s+(é|confirmado|definitivo)\b",
    r"\btome\s+\d+\s*(mg|ml|gotas)\b",
    r"\bpaciente\s+deve\s+tomar\s+\d+\s*(mg|ml|gotas)\b",
]


def _matches(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _normalize_word(word: str) -> str:
    folded = unicodedata.normalize("NFKD", word)
    return folded.encode("ascii", "ignore").decode("ascii").lower()


def _word_is_plausible(word: str) -> bool:
    w = _normalize_word(word)
    if not w:
        return False
    if w in _SHORT_OK_WORDS:
        return True
    if len(w) <= 2:
        return w in _SHORT_OK_WORDS
    if not any(c in _VOWELS for c in w):
        return False
    if re.search(r"[^aeiou]{6,}", w):
        return False
    return True


def _is_gibberish(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return True

    if re.fullmatch(r"[\d\s.,:/\-]+", raw):
        return False

    if re.search(r"\d", raw) and re.search(r"[a-zA-ZÀ-ÿ]{2,}", raw, re.IGNORECASE):
        return False

    if re.search(r"(.)\1{6,}", raw):
        return True

    alpha_words = re.findall(r"[a-zA-ZÀ-ÿ]+", raw, re.IGNORECASE)
    if not alpha_words:
        return len(raw) >= 2

    plausible = sum(1 for w in alpha_words if _word_is_plausible(w))
    if plausible == 0:
        return True

    if len(alpha_words) >= 3 and plausible / len(alpha_words) < 0.34:
        return True

    if len(raw) <= 4:
        return plausible == 0

    return False


def check_input(text: str) -> GuardrailResult:
    if _matches(text, URGENCY_PATTERNS):
        return GuardrailResult(False, "urgency", URGENCY_REPLY)
    if _matches(text, DIAGNOSIS_PATTERNS):
        return GuardrailResult(False, "diagnosis", DIAGNOSIS_REPLY)
    if _matches(text, PRESCRIPTION_PATTERNS):
        return GuardrailResult(False, "prescription", PRESCRIPTION_REPLY)
    if _is_gibberish(text):
        return GuardrailResult(False, "gibberish", GIBBERISH_REPLY)
    return GuardrailResult(True)


def check_output(text: str) -> GuardrailResult:
    if _matches(text, FORBIDDEN_OUTPUT_PATTERNS):
        return GuardrailResult(False, "forbidden_output", DIAGNOSIS_REPLY)
    return GuardrailResult(True)
