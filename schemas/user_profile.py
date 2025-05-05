from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class GenderType(str, Enum):
    male = "male"
    female = "female"

class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    active = "active"
    very_active = "very_active"

class UserProfileCreate(BaseModel):
    name: str
    age: int = Field(..., ge=0, le=120)
    gender: GenderType = Field(..., alias="sex")  # alias agregado
    weight: float = Field(..., ge=20, le=300)
    height: float = Field(..., ge=50, le=250)
    activity_level: ActivityLevel = Field(..., alias="activity")  # alias agregado

    model_config = ConfigDict(populate_by_name=True)  # habilita alias

class NutritionalRequirements(BaseModel):
    calories: int
    protein: int
    fat: int
    carbs: int

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
