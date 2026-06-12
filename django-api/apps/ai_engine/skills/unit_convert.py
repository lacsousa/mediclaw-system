_KG_LB = 2.20462
_CM_IN = 0.393701
_ML_FLOZ = 0.033814

CONVERSIONS = {
    ("kg", "lb"): lambda v: v * _KG_LB,
    ("lb", "kg"): lambda v: v / _KG_LB,
    ("cm", "in"): lambda v: v * _CM_IN,
    ("in", "cm"): lambda v: v / _CM_IN,
    ("ml", "fl_oz"): lambda v: v * _ML_FLOZ,
    ("fl_oz", "ml"): lambda v: v / _ML_FLOZ,
}


def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
    fn = CONVERSIONS.get((from_unit, to_unit))
    if not fn:
        raise ValueError(f"Conversão não suportada: {from_unit} → {to_unit}")
    return {"value": round(fn(value), 4), "unit": to_unit}
