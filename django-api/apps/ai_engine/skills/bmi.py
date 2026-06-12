from pydantic import BaseModel, Field


class BMIInput(BaseModel):
    weight_kg: float = Field(gt=0)
    height_cm: float = Field(gt=0)


def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    BMIInput(weight_kg=weight_kg, height_cm=height_cm)
    h = height_cm / 100
    bmi = round(weight_kg / (h * h), 2)
    if bmi < 18.5:
        cat = "abaixo_do_peso"
    elif bmi < 25:
        cat = "eutrofico"
    elif bmi < 30:
        cat = "sobrepeso"
    elif bmi < 35:
        cat = "obesidade_grau_1"
    elif bmi < 40:
        cat = "obesidade_grau_2"
    else:
        cat = "obesidade_grau_3"
    return {"bmi": bmi, "category": cat}
