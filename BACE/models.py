from pydantic import BaseModel
from typing import List, Optional

# Declare Models that will be used for processing data in/out with fastAPI requests/responses.

class CreateProfile(BaseModel):
    survey_id: str

    class Config:
        orm_mode=True

class DesignModel(BaseModel):
    design: list

    class Config:
        orm_mode=True    

class FindProfile(BaseModel):
    profile_id: int

    class Config:
        orm_mode=True

class ProfileIn(BaseModel):
    profile_id: int

    class Config:
        orm_mode=True

class UpdateProfile(BaseModel):
    profile_id: int
    answer: int

    class Config:
        orm_mode=True

