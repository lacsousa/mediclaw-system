import pytest

from apps.ai_engine.guardrails import (
    DIAGNOSIS_REPLY,
    GIBBERISH_REPLY,
    PRESCRIPTION_REPLY,
    URGENCY_REPLY,
    GuardrailResult,
    check_input,
    check_output,
)


class TestCheckInput:
    def test_normal_question_passes(self):
        result = check_input("Como melhorar meu sono?")
        assert result.allowed is True
        assert result.reason == ""

    def test_diagnosis_request_is_blocked(self):
        result = check_input("Qual é o meu diagnóstico baseado nesses sintomas?")
        assert result.allowed is False
        assert result.reason == "diagnosis"
        assert result.canned_reply == DIAGNOSIS_REPLY

    def test_diagnosis_variant_diagnostique(self):
        result = check_input("Por favor diagnostique o que tenho.")
        assert result.allowed is False
        assert result.reason == "diagnosis"

    def test_doctor_differential_question_passes(self):
        assert (
            check_input(
                "Paciente com febre há 3 dias e tosse seca. Quais hipóteses diferenciais considerar?"
            ).allowed
            is True
        )

    def test_doctor_clinical_opinion_passes(self):
        assert (
            check_input("Conduta sugerida para paciente com HAS descompensada?").allowed
            is True
        )

    def test_doctor_patient_urgency_report_blocked_as_urgency(self):
        result = check_input("Paciente com dor forte no peito e falta de ar")
        assert result.allowed is False
        assert result.reason == "urgency"

    def test_prescription_request_is_blocked(self):
        result = check_input("Que remédio devo tomar para dor de cabeça?")
        assert result.allowed is False
        assert result.reason == "prescription"
        assert result.canned_reply == PRESCRIPTION_REPLY

    def test_prescription_prescreva(self):
        result = check_input("Prescreva algo para minha tosse.")
        assert result.allowed is False
        assert result.reason == "prescription"

    def test_prescription_dosagem(self):
        result = check_input("Qual a dosagem de paracetamol para adultos?")
        assert result.allowed is False
        assert result.reason == "prescription"

    def test_urgency_keywords_short_circuit(self):
        result = check_input("Estou com dor forte no peito agora")
        assert result.allowed is False
        assert result.reason == "urgency"
        assert result.canned_reply == URGENCY_REPLY

    def test_urgency_falta_de_ar(self):
        result = check_input("Estou com falta de ar há 10 minutos.")
        assert result.allowed is False
        assert result.reason == "urgency"

    def test_urgency_desmaiei(self):
        result = check_input("Desmaiei na academia.")
        assert result.allowed is False
        assert result.reason == "urgency"

    def test_urgency_takes_priority_over_diagnosis(self):
        # urgency must short-circuit before diagnosis
        result = check_input("Desmaiei, qual é meu diagnóstico?")
        assert result.reason == "urgency"

    def test_health_tip_question_passes(self):
        assert check_input("Quantas horas de sono são recomendadas?").allowed is True

    def test_exercise_question_passes(self):
        assert check_input("Qual o melhor exercício para perder peso?").allowed is True

    def test_nutrition_question_passes(self):
        assert check_input("O que é uma dieta balanceada?").allowed is True

    def test_gibberish_keyboard_mash_blocked(self):
        result = check_input("asdfghjkl qwerty zxcvbn")
        assert result.allowed is False
        assert result.reason == "gibberish"
        assert result.canned_reply == GIBBERISH_REPLY

    def test_gibberish_symbols_blocked(self):
        result = check_input("!!! ??? @@@")
        assert result.allowed is False
        assert result.reason == "gibberish"

    def test_gibberish_repeated_chars_blocked(self):
        result = check_input("aaaaaaaaaa")
        assert result.allowed is False
        assert result.reason == "gibberish"

    def test_health_data_short_passes(self):
        assert check_input("80 kg").allowed is True
        assert check_input("homem").allowed is True
        assert check_input("Dormi 7 horas").allowed is True

    def test_gibberish_does_not_override_urgency(self):
        result = check_input("Desmaiei asdfgh")
        assert result.reason == "urgency"


class TestCheckOutput:
    def test_clean_output_passes(self):
        result = check_output("Dormir 7–9 horas por noite é recomendado.")
        assert result.allowed is True

    def test_cancer_diagnosis_in_output_blocked(self):
        result = check_output("Com base nos sintomas, você tem câncer.")
        assert result.allowed is False
        assert result.reason == "forbidden_output"

    def test_medication_dose_in_output_blocked(self):
        result = check_output("Tome 500mg de paracetamol a cada 8 horas.")
        assert result.allowed is False
        assert result.reason == "forbidden_output"

    def test_diabetes_in_output_blocked(self):
        result = check_output("Você tem diabetes tipo 2 com base nos dados.")
        assert result.allowed is False

    def test_infarto_in_output_blocked(self):
        result = check_output("Você tem infarto, ligue para o SAMU.")
        assert result.allowed is False

    def test_medication_ml_blocked(self):
        result = check_output("Tome 10ml desse xarope agora.")
        assert result.allowed is False

    def test_medication_drops_blocked(self):
        result = check_output("Tome 5 gotas desse remédio.")
        assert result.allowed is False

    def test_definitive_patient_diagnosis_in_output_blocked(self):
        result = check_output("O paciente tem diabetes tipo 2 confirmado.")
        assert result.allowed is False
        assert result.reason == "forbidden_output"

    def test_patient_must_take_dose_blocked(self):
        result = check_output("O paciente deve tomar 500 mg de paracetamol a cada 8 horas.")
        assert result.allowed is False
