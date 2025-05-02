from typing import Dict

def calculate_requirements(age, gender, weight, height, activity_level) -> Dict:
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_multipliers = {
        "sedentary": 1.2,
        "active": 1.55,
        "very_active": 1.725
    }

    calories = int(bmr * activity_multipliers.get(activity_level, 1.2))
    protein = int(weight * 1.8)
    fat = int((0.25 * calories) / 9)
    carbs = int((calories - (protein * 4 + fat * 9)) / 4)

    return {
        "calories": calories,
        "protein": protein,
        "fat": fat,
        "carbs": carbs
    }
