from datetime import date
from pydantic import BaseModel
class UserSchema(BaseModel):
    userID=int
    userName=str
    userPassword=str
    userRole=int