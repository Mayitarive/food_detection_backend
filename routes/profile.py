from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.user_profile import UserProfile
from schemas.user_profile import UserProfileCreate, UserProfileResponse, NutritionalRequirements
from utils.requirements import calculate_requirements

router = APIRouter()

@router.post("/profile/", response_model=UserProfileResponse)
def create_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    db_profile = db.query(UserProfile).filter(UserProfile.name == profile.name).first()
    
    if db_profile:
        for key, value in profile.dict().items():
            setattr(db_profile, key, value)
    else:
        db_profile = UserProfile(**profile.dict())
        db.add(db_profile)
    
    db.commit()
    db.refresh(db_profile)

    requirements = calculate_requirements(
        age=profile.age,
        gender=profile.gender,
        weight=profile.weight,
        height=profile.height,
        activity_level=profile.activity_level
    )

    return UserProfileResponse(
        id=db_profile.id,
        name=db_profile.name,
        age=db_profile.age,
        gender=db_profile.gender,
        weight=db_profile.weight,
        height=db_profile.height,
        activity_level=db_profile.activity_level,
        requirements=NutritionalRequirements(**requirements)
    )
