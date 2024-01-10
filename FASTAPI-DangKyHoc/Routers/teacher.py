from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT
from model import UserSchema,StudentSchema,TeacherSchema
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


@router.post("/update_teacher_information",dependencies=[Depends(JWTBearer())])
async def update_teacher(
    db: Session = Depends(get_database_session),
    teacher_ID: str = Form(...),
    teacherName: str = Form(...),
    teacherDOB: date = Form(...),
    teacherGender: str = Form(...),
    teacherAddress: str = Form(...),
    teacherPhone: str = Form(...),
    teacherDatejoin: date = Form(...),
):
    teacher_exists = db.query(exists().where(TeacherSchema.teacherID == teacher_ID)).scalar()

    teacher = db.query(TeacherSchema).get(teacher_ID)
    if teacher_exists:
   
        teacher.teacherName = teacherName
        teacher.teacherDOB = teacherDOB
        teacher.teacherGender = teacherGender
        teacher.teacherAddress = teacherAddress
        teacher.teacherPhone = teacherPhone
        teacher.teacherDatejoin = teacherDatejoin

        # Commit and refresh
        db.commit()
        db.refresh(teacher)

        return {
            "data": "Thông tin giáo viên được cập nhật thành công"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Thông tin giáo viên không có trong dữ liệu "})
