from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter,HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists,Integer
import base64
from sqlalchemy.orm import Session,joinedload
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
from model import CourseSchema, TeacherSchema, TermSchema, SubjectSchema,ClassSchema   
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

#Tạo chương trình học
@router.post("/create_course",dependencies=[Depends(JWTBearer())], summary="Tạo chương trình học")
async def create_course(
    db: Session = Depends(get_database_session),
    courseID: int = Form(...),
    subjectID: str = Form(...),
    className: str = Form(...),
    courseDate: int = Form(...),
    courseShiftStart: int = Form(...),
    courseShiftEnd: int = Form(...),
    courseRoom: str = Form(...),
    teacherID: str = Form(...),
    termID: str = Form(...)
):
    #Check có tồn tại môn học không
    subject_non_exists = db.query(exists().where(SubjectSchema.subjectID != subjectID)).scalar()
    #Check có bị trùng tên lớp không
    class_exists = db.query(exists().where(CourseSchema.className == className)).sclar()
    #Check có bị trùng lịch học không
    course_time = db.query(exists().where(CourseSchema.courseDate == courseDate
    and CourseSchema.courseShiftStart == courseShiftStart and CourseSchema.courseShiftEnd == courseShiftEnd 
    and CourseSchema.courseRoom == courseRoom)).scalar()
    
    if subject_non_exists:
        return JSONResponse(status_code=400, content={"message": "Không tìm thấy môn học!"})
    elif class_exists:
        return JSONResponse(status_code=400, content={"message": "Trùng tên lớp!"})
    elif course_time:
        return JSONResponse(status_code=400, content={"message": "Trùng thời gian học!"})

    courseSchema = CourseSchema(courseID = courseID, subjectID = subjectID, className = className,
    courseDate = courseDate, courseShiftStart = courseShiftStart, courseShiftEnd = courseShiftEnd,
    courseRoom = courseRoom, teacherID = teacherID, termID = termID)
    db.add(courseSchema)
    db.commit()
    db.refresh(courseSchema)
    return {
        "data": "Tạo chương trình học thành công!"
    }

#Sửa chương trình học
@router.put("/update_course",dependencies=[Depends(JWTBearer())], summary="Sửa chương trình học")
async def update_course(
    db: Session = Depends(get_database_session),
    courseID: int = Form(...),
    subjectID: str = Form(...),
    className: str = Form(...),
    courseDate: int = Form(...),
    courseShiftStart: int = Form(...),
    courseShiftEnd: int = Form(...),
    courseRoom: str = Form(...),
    teacherID: str = Form(...),
    termID: str = Form(...)
):
    subject_non_exists = db.query(exists().where(SubjectSchema.subjectID != subjectID)).scalar()
    course_exists = db.query(exists().where(CourseSchema.courseID == courseID)).scalar()
    course = db.query(CourseSchema).get(courseID)

    if course_exists:
        print(course)
        course_time = db.query(exists().where(CourseSchema.courseDate == courseDate
        and CourseSchema.courseShiftStart == courseShiftStart and CourseSchema.courseShiftEnd == courseShiftEnd 
        and CourseSchema.courseRoom == courseRoom)).scalar()

        if subject_non_exists:
            return JSONResponse(status_code=400, content={"message": "Không tìm thấy môn học!"})
        elif course_time:
            return JSONResponse(status_code=400, content={"message": "Trùng thời gian học!"})

        course.subjectID = subjectID
        course.className = className
        course.courseDate = courseDate
        course.courseShiftStart = courseShiftStart
        course.courseShiftEnd = courseShiftEnd
        course.courseRoom = courseRoom
        course.teacherID = teacherID
        course.termID = termID
        db.commit()
        db.refresh(course)
        return {
            "data": "Thông tin chương trình học đã được cập nhật!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin chương trình!"})

#Xóa chương trình học
@router.delete("/delete_course/{courseID}",dependencies=[Depends(JWTBearer())], summary="Xóa chương trình học")
async def delete_course(
    db: Session = Depends(get_database_session),
    courseID = int
):
    course_exists = db.query(exists().where(CourseSchema.courseID == courseID)).scalar()
    if course_exists:
        course = db.query(CourseSchema).get(courseID)
        db.delete(course)
        db.commit()
        return {
            "data": "Xóa lớp học thành công!"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không tồn tại lớp học!"
        )

#Xóa chương trình học theo kỳ
@router.delete("/delete_course_by_term/{termID}",dependencies=[Depends(JWTBearer())], summary="Xóa chương trình học theo kỳ")
async def delete_course_by_term(
    db: Session = Depends(get_database_session),
    termID = str
):
    term_exists = db.query(exists().where(CourseSchema.termID == termID)).scalar()
    delete_term = db.query(CourseSchema).filter(CourseSchema.termID == termID).all()
    if term_exists:
        for term in delete_term:
            db.delete(term)
        db.commit()
        return{
        "data": "Xóa danh sách TKB trường {termID} thành công!"
        }
    return JSONResponse(status_code=400, content={"message": "Không tồn tại học kỳ!"})

#Danh sách lớp theo kỳ  
@router.get("/course", summary="Lấy danh sách lớp theo kỳ")
def get_courses_with_subject_info(
    db: Session = Depends(get_database_session),
    termID: str=Header(...)
):
    courses = (
        db.query(
            CourseSchema.courseID,
            SubjectSchema.subjectName,
            CourseSchema.className,
            CourseSchema.courseDate,
            CourseSchema.courseShiftStart,
            CourseSchema.courseShiftEnd,
            CourseSchema.courseRoom,
            CourseSchema.termID 
        )
        .join(SubjectSchema, CourseSchema.subjectID == SubjectSchema.subjectID)
        .join(TeacherSchema, CourseSchema.teacherID==TeacherSchema.teacherID)
        .filter(CourseSchema.termID==termID).all()
    )

    result = []
    for course in courses:
        result.append(
            {   
              "courseID":course[0],
               "subjectName": course[1],
                "className": course[2],
                "courseDate": course[3],
                "courseShiftStart": course[4],
                "courseShiftEnd": course[5],
                "courseRoom": course[6],
                "termID": course[7],
            }
        )
    return {"courses": result}

#Lấy thông tin chương trình
@router.get("/course/{courseID}",dependencies=[Depends(JWTBearer())], summary="Lấy thông tin chương trình")
def get_courses_with_subject_info(courseID: int,
    db: Session = Depends(get_database_session)):
    course = (
        db.query(
            CourseSchema.courseID,
            CourseSchema.subjectID,
            SubjectSchema.subjectName,
            CourseSchema.className,
            CourseSchema.courseDate,
            CourseSchema.courseShiftStart,
            CourseSchema.courseShiftEnd,
            CourseSchema.courseRoom,
            CourseSchema.teacherID,
            TeacherSchema.teacherName,
            CourseSchema.termID
        )
        .join(SubjectSchema, CourseSchema.subjectID == SubjectSchema.subjectID)
        .join(TeacherSchema, CourseSchema.teacherID==TeacherSchema.teacherID)
        .filter(CourseSchema.courseID==courseID).first()
    )
    if course is None:
        return {"course": {}}
    result = {
                "courseID":course[0],
                "subjectID": course[1],
                "subjectName": course[2],
                "className": course[3],
                "courseDate": course[4],
                "courseShiftStart": course[5],
                "courseShiftEnd": course[6],
                "courseRoom": course[7],
                "teacherID": course[8],
                "teacherName":course[9],
                "termID": course[10],
            }
    return {"course": result}

#Lấy lớp theo môn
@router.get("/courses_by_subject_term/{studentID}/{subjectID}/{termID}",dependencies=[Depends(JWTBearer())], summary="Lấy lớp theo môn")
def get_courses_by_subject_term(
    studentID: str,
    subjectID: str,
    termID: str,
    db: Session = Depends(get_database_session)):
    courses = (
        db.query(
            CourseSchema.className,
            CourseSchema.courseDate,
            CourseSchema.courseShiftStart,
            CourseSchema.courseShiftEnd,
            CourseSchema.courseID
        )
        .select_from(CourseSchema)
        .filter(CourseSchema.subjectID == subjectID, CourseSchema.termID == termID).all()
    )

    result = []
    
    for course in courses:
        is_registered = db.query(exists().where(ClassSchema.studentID == studentID, ClassSchema.courseID == course[4], ClassSchema.status == 1)).scalar()
    
        result.append(
            {
                "className": course[0],
                "courseDate": course[1],
                "courseShiftStart": course[2],
                "courseShiftEnd": course[3],
                "courseID":course[4],
                "is_registered": is_registered
            }
        )

    return {"courses": result}
