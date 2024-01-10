from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter,HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists,Integer
import base64
from sqlalchemy.orm import Session,joinedload
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
from model import CourseSchema, TeacherSchema, TermSchema, SubjectSchema,ClassSchema,ExamSchema
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

#Tạo lịch thi
@router.post("/create_exam",dependencies=[Depends(JWTBearer())], summary="Tạo lịch thi")
async def create_exam(
    db: Session = Depends(get_database_session),
    subjectID: str = Form(...),
    termID: str = Form(...),
):
    #Check có tồn tại lớp không
    subject_exists = db.query(exists().where(CourseSchema.subjectID == subjectID, CourseSchema.termID == termID)).scalar()
    duplicated = db.query(exists().where(ExamSchema.subjectID == subjectID, ExamSchema.termID == termID)).scalar()
    if not duplicated:
        if subject_exists:
            examSchema = ExamSchema(subjectID = subjectID, termID = termID)
            db.add(examSchema)
            db.commit()
            db.refresh(examSchema)
            return {
                "data:" "Tạo lịch thi thành công!"
            }
        else:
            return JSONResponse(status_code=400, content={"message": "Không tìm thấy dữ liệu!"})
    else:
        return JSONResponse(status_code=400, content={"message": "Dữ liệu đã tồn tại!"})
    
#Sửa lịch thi
@router.put("/update_exam",dependencies=[Depends(JWTBearer())], summary="Sửa lịch thi")
async def update_exam(
    db: Session = Depends(get_database_session),
    examID: int = Form(...),
    examShiftStart: str = Form(...),
    examShiftEnd: str = Form(...),
    examDate: str = Form(...)
):
    #Check có tồn tại ID không
    exam_exists = db.query(exists().where(ExamSchema.examID == examID)).scalar()

    if exam_exists:
        exam = db.query(ExamSchema).get(examID)
        exam.examShiftStart = examShiftStart
        exam.examShiftEnd = examShiftEnd
        exam.examDate = examDate
        db.commit()
        db.refresh(exam)
        return {
            "data": "Thông tin lịch thi đã được cập nhật!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin!"})
    
#Xóa lịch thi
@router.delete("/delete_exam/{examID}",dependencies=[Depends(JWTBearer())], summary="Xóa lịch thi")
async def delete_grade(
    db: Session = Depends(get_database_session),
    examID = int
):
    #Check có tồn tại ID không
    exam_exists = db.query(exists().where(ExamSchema.examID == examID)).scalar()
    if exam_exists:
        exam = db.query(ExamSchema).get(examID)
        db.delete(exam)
        db.commit()
        return{
         "data": "Xóa lịch thi thành công"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin!"})
    
#Lịch thi toàn trường 
@router.get("/exam",summary="Lấy thông tin lịch thi toàn trường")
def get_exam_with_subject_info(
    db: Session = Depends(get_database_session),
    termID: str=Header(...)
):
    exams = (
        db.query(
            ExamSchema.examID,
            ExamSchema.subjectID,
            SubjectSchema.subjectName,
            ExamSchema.examShiftStart,
            ExamSchema.examShiftEnd,
            ExamSchema.examDate
 
        )
        .join(SubjectSchema, ExamSchema.subjectID == SubjectSchema.subjectID)
        .filter(ExamSchema.termID==termID).all()
    )

    result = []
    for exam in exams:
        result.append(
            {   
                "examID":exam[0],
                "subjectID": exam[1],
                "subjectName": exam[2],
                "examShiftStart": exam[3],
                "examShiftEnd": exam[4],
                "examDate": exam[5],
            }
        )
    return {"exams": result}