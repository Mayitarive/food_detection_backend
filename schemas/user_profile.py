from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Enums para sexo y nivel de actividad
class GenderType(str, Enum):
    male = "male"
    female = "female"

class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    active = "active"
    very_active = "very_active"

# Esquema de entrada (crear perfil)
class UserProfileCreate(BaseModel):
    name: str
    age: int = Field(..., ge=0, le=120)
    gender: GenderType = Field(..., alias="sex")
    weight: float = Field(..., ge=20, le=300)
    height: float = Field(..., ge=50, le=250)
    activity_level: ActivityLevel = Field(..., alias="activity")

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
    requirements: NutritionalRequirements

    class Config:
        from_attributes = True
