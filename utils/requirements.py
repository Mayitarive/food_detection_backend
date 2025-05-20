from typing import Dict

def calculate_requirements(age, gender, weight, height, activity_level, goal="mantener") -> Dict:
    # Calcular Tasa Metabólica Basal (TMB o BMR)
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Multiplicador de actividad física
    activity_multipliers = {
        "sedentary": 1.2,
        "active": 1.55,
        "very_active": 1.725
    }

    # Calorías base ajustadas por actividad
    calories = bmr * activity_multipliers.get(activity_level, 1.2)

    #  Ajuste según objetivo
    if goal == "subir":
        calories += 300  # Superávit calórico leve
    elif goal == "bajar":
        calories -= 300  # Déficit calórico leve

    calories = int(calories)

    # Macronutrientes (usando proporciones comunes)
    protein = int(weight * 1.8)
    fat = int((0.25 * calories) / 9)
    carbs = int((calories - (protein * 4 + fat * 9)) / 4)

    return {
        "calories": calories,
        "protein": protein,
        "fat": fat,
        "carbs": carbs
    }
