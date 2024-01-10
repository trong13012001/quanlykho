from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists,Integer, func
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
from model import CourseSchema, TeacherSchema, GroupSchema, SubjectSchema,ClassSchema   
from model import CourseSchema
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

#Tổng tiền từng môn
@router.get("/bill_by_subject/{StudentID}/{termID}",dependencies=[Depends(JWTBearer())], summary="Tổng tiền từng môn")
def get_bill_by_subject(StudentID: str,termID:str, db: Session = Depends(get_database_session)):
    bills = (
        db.query(
            ClassSchema.courseID,
            SubjectSchema.subjectID,
            SubjectSchema.subjectName,
            SubjectSchema.subjectCredit * SubjectSchema.Coefficient,
            ClassSchema.termID,
            (SubjectSchema.subjectCredit * SubjectSchema.Coefficient * 450000).cast(Integer)
        )
        .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
        .join(SubjectSchema, CourseSchema.subjectID == SubjectSchema.subjectID)
        .filter(ClassSchema.studentID == StudentID,ClassSchema.termID==termID, ClassSchema.status == 2)
        .all()
    )

    result = []
    for bill in bills:
        result.append(
            {
                "courseID": bill[0],
                "subjectID": bill[1],
                "subjectName": bill[2],
                "quantity":bill[3],
                "unit":450000,
                "termID": bill[4],
                "bill": bill[5],
            }
        )

    return {"bills": result}

#Tổng tiền theo kỳ
@router.get("/bill_by_term/{StudentID}/{termID}",dependencies=[Depends(JWTBearer())], summary="Tổng tiền theo kỳ")
def get_bill_by_term(
            StudentID: str,
            termID: str,
            db: Session = Depends(get_database_session)):
    bill = (
        db.query(
            ClassSchema.studentID,
            ClassSchema.termID,
            func.sum(SubjectSchema.subjectCredit * SubjectSchema.Coefficient * 450000).cast(Integer)
        )
        .select_from(ClassSchema)
        .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
        .join(SubjectSchema, CourseSchema.subjectID == SubjectSchema.subjectID)
        .filter(ClassSchema.studentID == StudentID, CourseSchema.termID == termID, ClassSchema.status == 2)
        .group_by(ClassSchema.studentID, ClassSchema.termID)
        .first()
    )
    if bill is None:
        return {"bill": {}}
    
    result = {
                "studentID": bill[0],
                "termID": bill[1],
                "termSum": bill[2]
            }
        

    return {"bill": result}

#Tổng tiền
@router.get("/bill_total/{StudentID}",dependencies=[Depends(JWTBearer())], summary="Tổng tiền")
def get_bill_total(
            StudentID: str,
            db: Session = Depends(get_database_session)):
    bill = (
        db.query(
            ClassSchema.studentID,
            func.sum(SubjectSchema.subjectCredit * SubjectSchema.Coefficient * 450000).cast(Integer)
        )
        .select_from(ClassSchema)
        .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
        .join(SubjectSchema, CourseSchema.subjectID == SubjectSchema.subjectID)
        .filter(ClassSchema.studentID == StudentID, ClassSchema.status == 2)
        .group_by(ClassSchema.studentID)
        .first()
    )
    if bill is None:
        return {"bill": {}}
    
    result =  {
                "studentID": bill[0],
                "termSum": bill[1]
            }
    
    return {"bill": result}



@router.get("/courseBill/{courseID}", dependencies=[Depends(JWTBearer())], summary="Lấy thông tin hóa đơn môn")
def get_courses_bill_info(courseID: int, db: Session = Depends(get_database_session)):
    bill = (
        db.query(
            ClassSchema.courseID,
            SubjectSchema.subjectID,
            SubjectSchema.subjectName,
            SubjectSchema.subjectCredit * SubjectSchema.Coefficient,
            ClassSchema.termID,
            (SubjectSchema.subjectCredit * SubjectSchema.Coefficient * 450000).cast(Integer)
        )
        .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
        .join(SubjectSchema, CourseSchema.subjectID == SubjectSchema.subjectID)
        .filter(ClassSchema.courseID == courseID, ClassSchema.status == 2)
        .first()
    )

    if bill is None:
        return {"bill": {}}

    result = {
        "courseID": bill[0],
        "subjectID": bill[1],
        "subjectName": bill[2],
        "quantity": bill[3],
        "unit": 450000,
        "termID": bill[4],
        "bill": bill[5],
    }

    return {"bill": result}
