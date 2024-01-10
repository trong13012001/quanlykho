from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists, func
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import decodeJWT
from model import StudentSchema, BranchSchema, YearSchema, BranchSubjectSchema
import schema
from database import SessionLocal, engine
import model
from datetime import date

router = APIRouter()  
model.Base.metadata.create_all(bind=engine)


def get_database_session():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

#Sửa thông tin sinh viên
@router.put("/update_student_information",dependencies=[Depends(JWTBearer())], summary="Sửa thông tin sinh viên")
async def update_student(
    db: Session = Depends(get_database_session),
    student_ID: str = Form(...),
    studentName: str = Form(...),
    studentDOB: date = Form(...),
    studentGender: str = Form(...),
    studentAddress: str = Form(...),
    studentPhone: str = Form(...),
    studentYearJoin: int = Form(...),
    studentParent: str = Form(...),
    branchID: int = Form(...),
    status: int = Form(...)
):
    
    student = db.query(StudentSchema).get(student_ID)
    branch = db.query(BranchSchema).get(branchID)
    if student and branch and (status == 0 or status == 1):
        branchFilter = db.query(BranchSchema).filter(BranchSchema.branchID==branchID).first()
        getGroup = branchFilter.groupEnd
        today= date.today()

        yearFilter = db.query(YearSchema).filter(YearSchema.yearID==date.today().year-1).first()
        if(today>yearFilter.yearEnd):
            yearFilter = db.query(YearSchema).filter(YearSchema.yearID==date.today().year).first()
        print(yearFilter.yearID)
        studentK = studentYearJoin - 1987
        current_year = yearFilter.yearID - studentYearJoin
        print(current_year)
        if status == 1:
            if current_year == 0:
                group = 3
            elif current_year == 1:
                group = 2
            elif current_year > 1:
                group = getGroup
            else:
                group = 3
        else:
            group = 0
           
        student.studentName = studentName
        student.studentDOB = studentDOB
        student.studentK = studentK
        student.studentGender = studentGender
        student.studentAddress = studentAddress
        student.studentPhone = studentPhone
        student.studentYearJoin = studentYearJoin
        student.studentParent = studentParent
        student.branchID = branchID
        student.group = group
        student.status = status

        # Commit and refresh
        db.commit()
        db.refresh(student)

        return {
            "data": "Thông tin sinh viên được cập nhật thành công!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Kiểm tra lại mã sinh viên, mã khoa, mã ngành hoặc trạng thái (0 = Thôi học, 1 = Bình thường)"})

#Sửa khoa của sinh viên
@router.put("/update_student_major_information",dependencies=[Depends(JWTBearer())], summary="Sửa khoa của sinh viên")
async def update_student(
    db: Session = Depends(get_database_session),
    student_ID: str = Form(...),
    branchID:int= Form(...),

):
    student_exists = db.query(exists().where(StudentSchema.studentID == student_ID)).scalar()

    student = db.query(StudentSchema).get(student_ID)
    if student_exists:
        studentFilter = db.query(StudentSchema).filter(StudentSchema.studentID==student_ID).first()
        branchFilter = db.query(BranchSchema).filter(BranchSchema.branchID==branchID).first()

        getGroup = branchFilter.groupEnd
        today = date.today()

        yearFilter = db.query(YearSchema).filter(YearSchema.yearID==date.today().year-1).first()
        if(today>yearFilter.yearEnd):
            yearFilter = db.query(YearSchema).filter(YearSchema.yearID==date.today().year).first()
        current_year = yearFilter.yearID - studentFilter.studentYearJoin
        if studentFilter.status == 1:
            if current_year == 0:
                group = 3
            elif current_year == 1:
                group = 2
            elif current_year > 1:
                group = getGroup
            else:
                group = 3
        else:
            group = 0
        
        student.branchID = branchID
        student.group = group
        db.commit()
        db.refresh(student)

        return {
            "data": "Thông tin ngành sinh viên được cập nhật thành công"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Thông tin sinh viên không có trong dữ liệu "})

