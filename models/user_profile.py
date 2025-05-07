from sqlalchemy import Column, Integer, String, Float, Enum
from database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    age = Column(Integer)
    gender = Column(Enum("male", "female", name="gender_types"))
    weight = Column(Float)
    height = Column(Float)
    activity_level = Column(
        Enum("sedentary", "active", "very_active", name="activity_levels")
    )

    # ✅ Nuevos campos para guardar requerimientos nutricionales
    required_calories = Column(Integer)
    required_protein = Column(Integer)
    required_carbs = Column(Integer)
    required_fat = Column(Integer)
