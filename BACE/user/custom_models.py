from pydantic import BaseModel, validator, root_validator
from typing import List, Optional

# Declare Models that will be used for processing data in/out in router_qualtrics_custom.py

# Responses return a dictionary
class ResponseModel(BaseModel):
    response: dict

    class Config:
        orm_mode=True

# Requests for different calls. Update these if you want to add optional information.
# Validator is used to return test feedback if you include the requestion parameter test equal to "test".

# Create Profile
class CreateRequest(BaseModel):
    survey_id: str
    test: Optional[str]

    @root_validator(pre=True)
    def check_test(cls, values):
        if values.get('test') ==  'test':
            values['survey_id'] = 'test_survey'
        return values

    class Config:
        orm_mode=True

# First Design
class FirstDesignRequest(BaseModel):
    profile_id: int = 0
    test: Optional[str]

    @root_validator(pre=True)
    def check_test(cls, values):

        if values.get('test') == 'test':
            values['profile_id'] = 0
            
        return values

    class Config:
        orm_mode=True

# Update and Choose
class UpdateChooseRequest(BaseModel):
    profile_id: int
    answer: int
    question_no: int
    test: Optional[str]

    @root_validator(pre=True)
    def check_test(cls, values):

        if values.get('test') == 'test':
            values['profile_id'] = 0
            values['answer'] = 0
            
        return values


    class Config:
        orm_mode=True

# Update and Return Estimates
class UpdateReturnEstimatesRequest(BaseModel):
    profile_id: int
    answer: int
    test: Optional[str]

    @root_validator(pre=True)
    def check_test(cls, values):

        if values.get('test') == 'test':
            values['profile_id'] = 0
            values['answer'] = 0
        return values

    class Config:
        orm_mode=True

