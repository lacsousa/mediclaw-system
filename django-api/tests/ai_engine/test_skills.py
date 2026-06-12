import pytest
from pydantic import ValidationError

from apps.ai_engine.skills.bmi import calculate_bmi
from apps.ai_engine.skills.unit_convert import convert_units


class TestCalculateBMI:
    def test_eutrofico(self):
        result = calculate_bmi(70, 175)
        assert result["bmi"] == 22.86
        assert result["category"] == "eutrofico"

    def test_abaixo_do_peso(self):
        result = calculate_bmi(50, 175)
        assert result["category"] == "abaixo_do_peso"

    def test_sobrepeso(self):
        result = calculate_bmi(85, 175)
        assert result["category"] == "sobrepeso"

    def test_obesidade_grau_1(self):
        result = calculate_bmi(105, 175)
        assert result["category"] == "obesidade_grau_1"

    def test_obesidade_grau_2(self):
        result = calculate_bmi(110, 175)  # BMI ≈ 35.9 → grau_2
        assert result["category"] == "obesidade_grau_2"

    def test_obesidade_grau_3(self):
        result = calculate_bmi(145, 175)
        assert result["category"] == "obesidade_grau_3"

    def test_bmi_is_rounded_to_two_decimals(self):
        result = calculate_bmi(70, 175)
        assert isinstance(result["bmi"], float)
        assert result["bmi"] == round(result["bmi"], 2)

    def test_invalid_zero_weight_raises(self):
        with pytest.raises(ValidationError):
            calculate_bmi(0, 175)

    def test_invalid_negative_height_raises(self):
        with pytest.raises(ValidationError):
            calculate_bmi(70, -1)

    def test_invalid_zero_height_raises(self):
        with pytest.raises(ValidationError):
            calculate_bmi(70, 0)


class TestConvertUnits:
    def test_kg_to_lb(self):
        result = convert_units(1.0, "kg", "lb")
        assert result["value"] == 2.2046
        assert result["unit"] == "lb"

    def test_lb_to_kg(self):
        result = convert_units(2.20462, "lb", "kg")
        assert result["value"] == 1.0
        assert result["unit"] == "kg"

    def test_cm_to_in(self):
        result = convert_units(100, "cm", "in")
        assert result["value"] == 39.3701
        assert result["unit"] == "in"

    def test_in_to_cm(self):
        result = convert_units(1.0, "in", "cm")
        assert abs(result["value"] - 2.5400) < 0.001
        assert result["unit"] == "cm"

    def test_ml_to_fl_oz(self):
        result = convert_units(100, "ml", "fl_oz")
        assert result["value"] == 3.3814
        assert result["unit"] == "fl_oz"

    def test_fl_oz_to_ml(self):
        result = convert_units(1.0, "fl_oz", "ml")
        assert abs(result["value"] - 29.5735) < 0.01
        assert result["unit"] == "ml"

    def test_unsupported_pair_raises(self):
        with pytest.raises(ValueError, match="não suportada"):
            convert_units(1.0, "kg", "cm")

    def test_unsupported_unknown_unit_raises(self):
        with pytest.raises(ValueError):
            convert_units(1.0, "xyz", "abc")
