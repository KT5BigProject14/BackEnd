from pydantic import BaseModel, EmailStr

class User(BaseModel):
    name: str
    email: EmailStr
    hashed_password: str
    phone: str

    class Config:
        orm_mode = True
