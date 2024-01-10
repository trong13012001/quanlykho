from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists,Integer, func
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
from model import ClassSchema, GradeSchema, SubjectSchema, StudentExamSchema, ExamSchema
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

#Đăng ký thi lại
@router.post("/create_student_re_exam",dependencies=[Depends(JWTBearer())], summary="Đăng ký thi lại")
async def create_student_exam(
    db: Session = Depends(get_database_session),
    studentID: str = Form(...),
    examID: int = Form(...)
):
    #Check có tồn tại môn học không
    student_exists = db.query(exists().where(ClassSchema.studentID == studentID)).scalar()
    exam_exists = db.query(exists().where(ExamSchema.examID == examID)).scalar()
    subject_exists = db.query(exists().where(ExamSchema.examID == examID, ExamSchema.subjectID == GradeSchema.subjectID,
                                             ExamSchema.termID != GradeSchema.termID)).scalar()

    duplicated = db.query(exists().where(StudentExamSchema.studentID == studentID,
                                          StudentExamSchema.examID == examID)).scalar()
    if not (duplicated and subject_exists):
        if student_exists and exam_exists:
            studentExamSchema = StudentExamSchema(studentID = studentID, examID = examID)
            db.add(studentExamSchema)
            db.commit()
            db.refresh(studentExamSchema)
            return JSONResponse(status_code=200, content={"message": "Đăng ký thi thành công!"})
        else:
            return JSONResponse(status_code=400, content={"message": "Không tìm thấy dữ liệu!"})
    else:
        return JSONResponse(status_code=400, content={"message": "Dữ liệu đã tồn tại!"})
    
#Hủy đăng ký thi lại
@router.delete("/delete_student_re_exam/{id}",dependencies=[Depends(JWTBearer())], summary="Hủy đăng ký thi lại")
async def delete_student_exam(
    db: Session = Depends(get_database_session),
    id = int
):
    student_exam_exists = db.query(exists().where(StudentExamSchema.id == id)).scalar()
    if student_exam_exists:
        student_exam = db.query(StudentExamSchema).get(id)
        db.delete(student_exam)
        db.commit()
        return JSONResponse(status_code=200, content={"message": "Hủy đăng ký thi thành công!"})
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin!"})

#Lịch thi
@router.get("/student_exam_by_student/{studentID}/{termID}",dependencies=[Depends(JWTBearer())], summary="Lịch thi")
def get_student_exam_by_student(
    db: Session = Depends(get_database_session),
    studentID = str,
    termID = str
):
    #Check có tồn tại sinh viên không
    student_exists = db.query(exists().where(StudentExamSchema.studentID == studentID)).scalar()
    #Check có học kỳ không
    term_exists = db.query(exists().where(ExamSchema.termID == termID)).scalar()

    if not (student_exists and term_exists):
        return JSONResponse(status_code=400, content={"message": "Không có thông tin!"})
    studentExams = (
        db.query(
            ExamSchema.subjectID,
            SubjectSchema.subjectName,
            ExamSchema.examShiftStart,
            ExamSchema.examShiftEnd,
            ExamSchema.examDate
        )
        .select_from(StudentExamSchema)
        .join(ExamSchema, StudentExamSchema.examID == ExamSchema.examID)
        .join(SubjectSchema, ExamSchema.subjectID == SubjectSchema.subjectID)
        .filter(StudentExamSchema.studentID == studentID, ExamSchema.termID == termID, StudentExamSchema.status == 2).all() 
    )

    result = []
    for studentExam in studentExams:
        result.append(
            {   
                "subjectID": studentExam[0],
                "subjectName": studentExam[1],
                "examShiftStart": studentExam[2],
                "examShiftEnd": studentExam[3],
                "examDate": studentExam[4],
            }
        )
    return {"studentExam": result}

#Danh sách môn thi lại
@router.get("/student_re_exam_by_student/{studentID}",dependencies=[Depends(JWTBearer())], summary="Danh sách môn thi lại")
def get_student_re_exam_by_student(
    db: Session = Depends(get_database_session),
    studentID = str
):
    #Check có tồn tại sinh viên không
    student_exists = db.query(exists().where(StudentExamSchema.studentID == studentID)).scalar()

    if not (student_exists):
        return JSONResponse(status_code=400, content={"message": "Không có thông tin!"})
    studentExams = (
        db.query(
            ExamSchema.subjectID,
            SubjectSchema.subjectName,
        )
        .select_from(GradeSchema)
        .join(ExamSchema, GradeSchema.subjectID == ExamSchema.subjectID)
        .join(SubjectSchema, ExamSchema.subjectID == SubjectSchema.subjectID)
        .filter(GradeSchema.studentID == studentID, GradeSchema.finalGrade >= 0)
        .distinct()
        .all() 
    )

    result = []
    for studentExam in studentExams:
        result.append(
            {   
                "subjectID": studentExam[0],
                "subjectName": studentExam[1]
            }
        )
    return {"studentExam": result}