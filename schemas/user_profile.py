from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Enums para sexo, nivel de actividad y objetivo
class GenderType(str, Enum):
    male = "male"
    female = "female"

class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    active = "active"
    very_active = "very_active"
#incluir goal
class GoalType(str, Enum):
    mantener = "mantener"
    subir = "subir"
    bajar = "bajar"

# Esquema de entrada (crear perfil)
class UserProfileCreate(BaseModel):
    name: str
    age: int = Field(..., ge=0, le=120)
    gender: GenderType = Field(..., alias="sex")
    weight: float = Field(..., ge=20, le=300)
    height: float = Field(..., ge=50, le=250)
    activity_level: ActivityLevel = Field(..., alias="activity")
    goal: GoalType = Field(..., alias="goal")

    model_config = ConfigDict(populate_by_name=True)

# Esquema para los requerimientos nutricionales
class NutritionalRequirements(BaseModel):
    calories: int
    protein: int
    fat: int
    carbs: int

# Esquema de salida (respuesta del perfil)
class UserProfileResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: GenderType
    weight: float
    height: float
    activity_level: ActivityLevel
    goal: GoalType
    requirements: NutritionalRequirements

    class Config:
        from_attributes = True
