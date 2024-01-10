from datetime import date
from pydantic import BaseModel
class UserSchema(BaseModel):
    userID=int
    userName=str
    userPassword=str
    userRole=int
class ProductSchema(BaseModel):
    productId=int
    productName=str
    category=str
    brand=str
    serial=str
    description=str
    quantityInStock=str
    unitPrice=str