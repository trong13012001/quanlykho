from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import decodeJWT
from model import UserSchema
import schema
from database import SessionLocal, engine
import model


router = APIRouter()  
model.Base.metadata.create_all(bind=engine)


def get_database_session():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@router.get("/user",dependencies=[Depends(JWTBearer())])
async def get_user(
    authorization: str = Header(...),
    db: Session = Depends(get_database_session),
):  
    
    user = decodeJWT(authorization.split()[1])
    userID = user.get("user_id")

    user = db.query(UserSchema).filter_by(userName=userID).first()
    return {"user": user}