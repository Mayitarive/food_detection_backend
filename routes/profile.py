from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies import get_db
from models.user_profile import UserProfile
from schemas.user_profile import UserProfileCreate, UserProfileResponse, NutritionalRequirements
from utils.requirements import calculate_requirements

router = APIRouter()

@router.post("/profile/", response_model=UserProfileResponse)
def create_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    db_profile = db.query(UserProfile).filter(UserProfile.name == profile.name).first()
    
    # Calcular requerimientos
    requirements = calculate_requirements(
        age=profile.age,
        gender=profile.gender,
        weight=profile.weight,
        height=profile.height,
        activity_level=profile.activity_level
    )

    if db_profile:
        for key, value in profile.dict().items():
            setattr(db_profile, key, value)
        # También actualizar los requerimientos
        db_profile.required_calories = requirements["calories"]
        db_profile.required_protein = requirements["protein"]
        db_profile.required_carbs = requirements["carbs"]
        db_profile.required_fat = requirements["fat"]
    else:
        db_profile = UserProfile(
            **profile.dict(),
            required_calories=requirements["calories"],
            required_protein=requirements["protein"],
            required_carbs=requirements["carbs"],
            required_fat=requirements["fat"]
        )
        db.add(db_profile)

    db.commit()
    db.refresh(db_profile)

    return UserProfileResponse(
        id=db_profile.id,
        name=db_profile.name,
        age=db_profile.age,
        gender=db_profile.gender,
        weight=db_profile.weight,
        height=db_profile.height,
        activity_level=db_profile.activity_level,
        requirements=NutritionalRequirements(
            calories=db_profile.required_calories,
            protein=db_profile.required_protein,
            carbs=db_profile.required_carbs,
            fat=db_profile.required_fat
        )
    )
