from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists,Integer, func
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
from model import StudentSchema, TermSchema, ClassSchema, GradeSchema, SubjectSchema
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

#Tạo điểm môn học
@router.post("/create_grade",dependencies=[Depends(JWTBearer())], summary="Tạo điểm môn học")
async def create_grade(
    db: Session = Depends(get_database_session),
    studentID: str = Form(...),
    termID: str = Form(...),
    subjectID: str = Form(...),
):
    #Check có tồn tại sinh viên không
    student_exists = db.query(exists().where(ClassSchema.studentID == studentID)).scalar()
    #Check có học kỳ không
    term_exists = db.query(exists().where(ClassSchema.termID == termID)).scalar()
    duplicated = db.query(exists().where(GradeSchema.studentID == studentID,
                                          GradeSchema.termID == termID, GradeSchema.subjectID == subjectID)).scalar()
    if not duplicated:
        if student_exists and term_exists:
            gradeSchema = GradeSchema(studentID = studentID, termID = termID, subjectID = subjectID)
            db.add(gradeSchema)
            db.commit()
            db.refresh(gradeSchema)
            return {
                "data:" "Tạo điểm môn học thành công!"
            }
        else:
            return JSONResponse(status_code=400, content={"message": "Không tìm thấy dữ liệu!"})
    else:
        return JSONResponse(status_code=400, content={"message": "Dữ liệu đã tồn tại!"})

#Sửa điểm môn học
@router.put("/update_grade",dependencies=[Depends(JWTBearer())], summary="Sửa điểm môn học")
async def update_grade(
    db: Session = Depends(get_database_session),
    gradeID: int = Form(...),
    studentID: str = Form(...),
    termID: str = Form(...),

    subjectID: str = Form(...),

    progressGrade: float = Form(...),
    examGrade1: float = Form(...),
    examGrade2: float = Form(...),
):
    #Check có tồn tại ID không
    grade_exist = db.query(exists().where(GradeSchema.gradeID == gradeID)).scalar()
    #Check có tồn tại môn học không
    student_exists = db.query(exists().where(GradeSchema.studentID == studentID)).scalar()
    #Check có bị trùng môn không
    class_exists = db.query(exists().where(GradeSchema.subjectID == subjectID)).scalar()

    #Check có học kỳ không
    term_exists = db.query(exists().where(GradeSchema.termID == termID)).scalar()
    finalGrade = (progressGrade*0.3) + (examGrade1*0.7)
    #Nếu điểm QT không đủ
    if (progressGrade < 4):
        finalGrade = -1
    #Nếu có điểm thi 2
    elif (examGrade2 > 0):
        finalGrade = (progressGrade*0.3) + (((examGrade1 + examGrade2)/2)*0.7)
    if grade_exist and class_exists and term_exists:
        grade = db.query(GradeSchema).get(gradeID)

        if student_exists and class_exists and term_exists:
            grade.gradeID = gradeID
            grade.studentID = studentID
            grade.termID = termID

            grade.subjectID = subjectID

            grade.progressGrade = progressGrade
            grade.examGrade1 = examGrade1
            grade.examGrade2 = examGrade2
            grade.finalGrade = finalGrade
            db.commit()
            db.refresh(grade)
            return {
                "data": "Thông tin điểm môn học đã được cập nhật!"
            }
        else:
            return JSONResponse(status_code=400, content={"message": "Thông tin không chính xác!"})
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin!"})

#Xóa điểm
@router.delete("/delete_grade/{gradeID}",dependencies=[Depends(JWTBearer())], summary="Xóa điểm")
async def delete_grade(
    db: Session = Depends(get_database_session),
    gradeID = int
):
    grade_exists = db.query(exists().where(GradeSchema.gradeID == gradeID)).scalar()
    if grade_exists:
        grade = db.query(GradeSchema).get(gradeID)
        db.delete(grade)
        db.commit()
        return{
         "data": "Xóa điểm thành công!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin!"})

#Phiếu báo điểm
@router.get("/grade_by_student_and_term/{termID}/{studentID}",dependencies=[Depends(JWTBearer())], summary="Phiếu báo điểm")
def get_grade_by_student_and_term(
    db: Session = Depends(get_database_session),
    studentID = str,
    termID = str
):
    #Check có tồn tại sinh viên không
    student_exists = db.query(exists().where(GradeSchema.studentID == studentID)).scalar()
    #Check có học kỳ không
    term_exists = db.query(exists().where(GradeSchema.termID == termID)).scalar()

    if student_exists and term_exists:
        grades = (
            db.query(
                GradeSchema.gradeID,
                GradeSchema.studentID,
                GradeSchema.progressGrade,
                GradeSchema.examGrade1,
                GradeSchema.examGrade2,
                GradeSchema.finalGrade,
                SubjectSchema.subjectName,
            )
            .select_from(GradeSchema)
            .join(SubjectSchema, SubjectSchema.subjectID == GradeSchema.subjectID)
            .filter(GradeSchema.studentID == studentID, GradeSchema.termID == termID, GradeSchema.status != 0).all() 
        )

        result = []
        for grade in grades:
            result.append(
                {   
                    "gradeID":grade[0],
                    "courseID": grade[1],
                    "progressGrade": grade[2],
                    "examGrade1": grade[3],
                    "examGrade2": grade[4],
                    "finalGrade": grade[5],
                    "subjectName":grade[6]

                }
            )
        return {"studentTermGrade": result}
    
#Bảng điểm
@router.get("/get_final_grade_by_student",dependencies=[Depends(JWTBearer())], summary="Bảng điểm")
def get_gfinal_grade_by_student(
    db: Session = Depends(get_database_session),
    studentID: str=Header(...)
):
    #Check có tồn tại sinh viên không
    student_exists = db.query(exists().where(GradeSchema.studentID == studentID)).scalar()

    if student_exists:
        grades = (
            db.query(
                GradeSchema.gradeID,
                GradeSchema.subjectID,
                GradeSchema.finalGrade,
                SubjectSchema.subjectName,
                SubjectSchema.subjectCredit,
            )
            .select_from(GradeSchema)
            .join(SubjectSchema, GradeSchema.subjectID == SubjectSchema.subjectID)
            .filter(GradeSchema.studentID == studentID, GradeSchema.status == 2)
        )

        result = []
        for grade in grades:
            result.append(
                {   
                    "gradeID":grade[0],
                    "subjectID": grade[1],
                    "finalGrade": grade[2],
                    "subjectName":grade[3],
                    "subjectCredit":grade[4]
                }
            )
        return {"grades": result}
    
#Điểm TB và tổng tín chỉ
@router.get("/get_avg_grade_and_credit",dependencies=[Depends(JWTBearer())], summary="Điểm TB và tổng tín chỉ")
def get_avg_grade_and_credit(
    db: Session = Depends(get_database_session),
    studentID: str=Header(...)
):
    #Check có tồn tại sinh viên không
    student_exists = db.query(exists().where(GradeSchema.studentID == studentID)).scalar()

    if student_exists:
        grade = (
            db.query(
                GradeSchema.studentID,
                func.avg(GradeSchema.finalGrade),
                func.sum(SubjectSchema.subjectCredit)
            )
            .select_from(GradeSchema)
            .join(SubjectSchema, GradeSchema.subjectID == SubjectSchema.subjectID)
            .filter(GradeSchema.studentID == studentID, GradeSchema.finalGrade >=4, GradeSchema.status == 2)
            .group_by(GradeSchema.studentID)
            .first()
        )

        if grade is None:
            return {"grade": {}}
        
        result =  {   
                    "studentID":grade[0],
                    "avgGrade": grade[1],
                    "totalCredit": grade[2]
                }

        return {"grade": result}