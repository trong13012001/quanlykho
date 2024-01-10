from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists
from sqlalchemy.orm import Session
from auth.auth_bearer import JWTBearer
from model import YearSchema
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

@router.post("/create_year",dependencies=[Depends(JWTBearer())])
async def create_year(
    db: Session = Depends(get_database_session),
    yearID: int = Form(...)
):
    year_exists = db.query(exists().where(YearSchema.yearID == yearID)).scalar()
    if year_exists:
        return {"data": "Trùng năm học!"}
    yearSchema = YearSchema(yearID = yearID)
    db.add(yearSchema)
    db.commit()
    db.refresh(yearSchema)
    return{
        "data": "Tạo năm học thành công!"
    }

@router.post("/delete_year",dependencies=[Depends(JWTBearer())])
async def delete_year(
    db: Session = Depends(get_database_session),
    yearID: int = Form(...)
):
    year_exists = db.query(exists().where(YearSchema.yearID == yearID)).scalar()
    if year_exists:
        year = db.query(YearSchema).get(yearID)
        db.delete(year)
        db.commit()
        return{
         "data": "Xóa năm học thành công!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không tồn tại năm học!"})