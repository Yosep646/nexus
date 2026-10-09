from pydantic import BaseModel, Field

class ReviewRequest(BaseModel):
    decision: str = Field(pattern='^(confirmed|dismissed)$')
    notes: str = Field(default='', max_length=1000)

class CameraCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    url: str = Field(min_length=7, max_length=2048)
