from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
from model import ClassSchema, CourseSchema, StudentSchema, TermSchema, SubjectSchema, BranchSubjectSchema,GradeSchema, ExamSchema, StudentExamSchema
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


#Đăng ký học
@router.post("/create_class",dependencies=[Depends(JWTBearer())], summary="Đăng ký học")
async def create_class(
    db: Session = Depends(get_database_session),
    studentID: str = Form(...),
    courseID: int = Form(...),
    termID: str = Form(...)
):
    #Check có tồn tại chương trình không
    course_exists = db.query(exists().where(CourseSchema.courseID == courseID, TermSchema.termID == termID)).scalar()
    #Check có tồn tại MSV không
    student_exists = db.query(exists().where(StudentSchema.studentID == studentID)).scalar()
    #Check đã từng đăng ký chưa
    class_exists = db.query(exists().where(ClassSchema.courseID == courseID, ClassSchema.termID == termID)).scalar()

    #Nếu đã từng đăng ký xong hủy
    if class_exists:
        #Lấy lịch từ môn đã đăng ký
        courseFilter = (
            db.query(
                CourseSchema.courseDate,
                CourseSchema.courseShiftStart,
                CourseSchema.courseShiftEnd
            )
            .select_from(ClassSchema)
            .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
            .filter(ClassSchema.studentID == studentID, ClassSchema.termID == termID, ClassSchema.status != 0).all()
        )

        #Lấy lớp đã chọn
        chosenCourseFilter = db.query(CourseSchema).filter(CourseSchema.courseID == courseID, CourseSchema.termID == termID).first()

        #Đưa ca vào mảng, khoanh vùng ca của lớp nếu trùng ngày với lớp đã chọn
        courseTime = [list(range(array[1], array[2]+1)) for array in courseFilter if array[0] == chosenCourseFilter.courseDate]
        print(courseTime)

        #Kiểm tra ca bắt đầu hoặc kết thúc của lớp đã chọn có nằm trong mảng nào không
        for i in courseTime:
            if (chosenCourseFilter.courseShiftStart in i or chosenCourseFilter.courseShiftEnd in i):
                return JSONResponse(status_code=400, content={"message": "Trùng lịch!"})       
        classid = (db.query
                   (
            ClassSchema.classID
            )
            .select_from(ClassSchema)

            .filter(ClassSchema.studentID == studentID, ClassSchema.courseID == courseID, ClassSchema.termID == termID, ClassSchema.status == 0).first()

        )
        examid1 = (db.query
                   (
                    StudentExamSchema.id,
                   )
                   .select_from(StudentExamSchema)
                   .join(ExamSchema, StudentExamSchema.examID == ExamSchema.examID)
                   .join(CourseSchema, ExamSchema.subjectID == CourseSchema.subjectID)
                   .filter(ClassSchema.studentID == studentID, CourseSchema.courseID == courseID, ExamSchema.termID == termID, StudentExamSchema.status == 0).first()
        )
        gradeid = (db.query
                   (
                    GradeSchema.gradeID,
                   )
                   .select_from(GradeSchema)
                   .join(SubjectSchema, SubjectSchema.subjectID == GradeSchema.subjectID)
                   .join(CourseSchema, SubjectSchema.subjectID == CourseSchema.subjectID)
                   .filter(ClassSchema.studentID == studentID, CourseSchema.courseID == courseID, GradeSchema.termID == termID, GradeSchema.status == 0).first()
        )
        get_class = db.query(ClassSchema).get(classid)
        get_exam = db.query(StudentExamSchema).get(examid1)
        get_grade = db.query(GradeSchema).get(gradeid)

        get_class.status = 1
        get_exam.status = 1
        get_grade.status = 1
        db.commit()
        db.refresh(get_class)
        db.refresh(get_exam)
        db.refresh(get_grade)
        return JSONResponse(status_code=200, content={"message": "Đăng ký môn thành công!"})
    
    #Nếu đăng ký mới
    elif course_exists and student_exists:
        #Lấy mã môn từ course
        subjectFilter = db.query(CourseSchema).filter(CourseSchema.courseID == courseID).first()
        subjectID = subjectFilter.subjectID

        #Lấy lịch từ môn đã đăng ký
        courseFilter = (
            db.query(
                CourseSchema.courseDate,
                CourseSchema.courseShiftStart,
                CourseSchema.courseShiftEnd
            )
            .select_from(ClassSchema)
            .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
            .filter(ClassSchema.studentID == studentID, ClassSchema.termID == termID, ClassSchema.status != 0).all()
        )

        #Lấy lớp đã chọn
        chosenCourseFilter = db.query(CourseSchema).filter(CourseSchema.courseID == courseID, CourseSchema.termID == termID).first()

        #Đưa ca vào mảng, khoanh vùng ca của lớp nếu trùng ngày với lớp đã chọn
        courseTime = [list(range(array[1], array[2]+1)) for array in courseFilter if array[0] == chosenCourseFilter.courseDate]
        print(courseTime)

        #Kiểm tra ca bắt đầu hoặc kết thúc của lớp đã chọn có nằm trong mảng nào không
        for i in courseTime:
            if (chosenCourseFilter.courseShiftStart in i or chosenCourseFilter.courseShiftEnd in i):
                return JSONResponse(status_code=400, content={"message": "Trùng lịch!"})
            
        classSchema = ClassSchema(courseID = courseID, studentID = studentID, termID = termID, status = 1)
        gradeSchema = GradeSchema(studentID = studentID, termID = termID, subjectID = subjectID, status = 1)
        examFilter = db.query(ExamSchema).filter(ExamSchema.subjectID == subjectID, ExamSchema.termID == termID).first()
        examid = examFilter.examID
        examSchema = StudentExamSchema(studentID = studentID, examID = examid, status = 1)

        db.add(classSchema)
        db.add(gradeSchema)
        db.add(examSchema)
        db.commit()
        db.refresh(classSchema)
        db.refresh(gradeSchema)
        db.refresh(examSchema)
        return JSONResponse(status_code=200, content={"message": "Đăng ký môn thành công!"})

    else:
        return JSONResponse(status_code=400, content={"message": "Error!"})
    
#Hủy đăng ký
@router.put("/update_class",dependencies=[Depends(JWTBearer())], summary="Hủy đăng ký")
async def update_class(
    db: Session = Depends(get_database_session),
    courseID: int = Form(...),
    studentID: str = Form(...),
    termID:str=Form(...)
):
    student_exists = db.query(exists().where(StudentSchema.studentID == studentID)).scalar()
    class_exists = db.query(exists().where(ClassSchema.studentID == studentID, ClassSchema.courseID == courseID, ClassSchema.termID == termID, ClassSchema.status == 0)).scalar()
    if class_exists:
        return JSONResponse(status_code=400, content={"message": "Error!"})
    classID=(
            db.query(
            ClassSchema.classID
        )
            .select_from(ClassSchema)
            .filter(ClassSchema.studentID == studentID, ClassSchema.studentID==studentID, ClassSchema.termID==termID, ClassSchema.courseID==courseID, ClassSchema.status == 1).first())


    examid = (db.query
            (
            StudentExamSchema.id,
            )
            .select_from(ClassSchema)
            .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
            .join(ExamSchema, CourseSchema.subjectID == ExamSchema.subjectID)
            .join(StudentExamSchema, ExamSchema.examID == StudentExamSchema.examID)
            .filter(ClassSchema.studentID == studentID, ClassSchema.studentID==studentID,ClassSchema.termID==termID,ClassSchema.courseID==courseID, StudentExamSchema.status == 1).first()
            )
    gradeid = (db.query
            (
            GradeSchema.gradeID,
            )
            .select_from(ClassSchema)
            .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
            .join(GradeSchema, CourseSchema.subjectID == GradeSchema.subjectID)
            .filter(ClassSchema.studentID == studentID, ClassSchema.studentID==studentID,ClassSchema.termID==termID,ClassSchema.courseID==courseID, GradeSchema.status == 1).first()
        )

    get_class = db.query(ClassSchema).get(classID)
    get_exam = db.query(StudentExamSchema).get(examid)
    get_grade = db.query(GradeSchema).get(gradeid)

    if student_exists:
        get_class.status = 0
        get_exam.status = 0
        get_grade.status = 0
        db.commit()
        db.refresh(get_class)
        db.refresh(get_exam)
        db.refresh(get_grade)
        return JSONResponse(status_code=200, content={"message": "Hủy đăng ký môn thành công!"})
    else:
        return JSONResponse(status_code=400, content={"message": "Kiểm tra lại thông tin!"})

#Đăng ký lớp khác (Suspended)
@router.put("/update_new_class",dependencies=[Depends(JWTBearer())], summary="Đăng ký lớp khác (Tạm bỏ)")
async def update_new_class(
    db: Session = Depends(get_database_session),
    classID: int = Form(...),
    studentID: str = Form(...),
    courseID: int = Form(...),
    termID: str = Form(...),

):
    course_exists = db.query(exists().where(CourseSchema.courseID == courseID)).scalar()
    student_exists = db.query(exists().where(StudentSchema.studentID == studentID)).scalar()
    courseClass = db.query(ClassSchema).get(classID)

    registered = (
        db.query(CourseSchema.subjectID)
        .select_from(ClassSchema)
        .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
        .all()
    )

    registering = db.query(CourseSchema).filter(CourseSchema.courseID == courseID, CourseSchema.termID == termID).first()

    registeredCourse = [subject[0] for subject in registered]
    print(registeredCourse)

    if registering.subjectID not in registeredCourse:
        print(registering.subjectID)
        return JSONResponse(status_code=400, content={"message": "Error!"})
    if course_exists and student_exists:
        courseClass.courseID = courseID
        courseClass.status = 1
        db.commit()
        db.refresh(courseClass)
        return JSONResponse(status_code=200, content={"message": "Đăng ký môn thành công!"})
    else:
        return JSONResponse(status_code=400, content={"message": "Kiểm tra lại thông tin!"})

#Xóa sinh viên trong lớp
@router.delete("/delete_class",dependencies=[Depends(JWTBearer())], summary="Xóa sinh viên trong lớp")
async def delete_class(
    db: Session = Depends(get_database_session),
    classID: int = Form(...)
):
    class_exists = db.query(exists().where(ClassSchema.classID == classID)).scalar()
    examid = (db.query
            (
            StudentExamSchema.id,
            )
            .select_from(ClassSchema)
            .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
            .join(ExamSchema, CourseSchema.subjectID == ExamSchema.subjectID)
            .join(StudentExamSchema, ExamSchema.examID == StudentExamSchema.examID)
            .filter(ClassSchema.classID == classID).first()
            )
    gradeid = (db.query
            (
            GradeSchema.gradeID,
            )
            .select_from(ClassSchema)
            .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
            .join(GradeSchema, CourseSchema.subjectID == GradeSchema.subjectID)
            .filter(ClassSchema.classID == classID).first()
        )
    
    if class_exists:
        class_delete = db.query(ClassSchema).get(classID)
        exam_delete = db.query(StudentExamSchema).get(examid)
        grade_delete = db.query(GradeSchema).get(gradeid)
        db.delete(class_delete)
        db.delete(exam_delete)
        db.delete(grade_delete)
        db.commit()
        db.refresh(class_delete)
        db.refresh(exam_delete)
        db.refresh(grade_delete)
        return JSONResponse(status_code=200, content={"message": "Xóa lớp thành công!"})
    else:
        return JSONResponse(status_code=400, content={"message": "Không tồn tại lớp học!"})

#Xóa sinh viên hủy đăng ký
@router.delete("/delete_class_no_register",dependencies=[Depends(JWTBearer())], summary="Xóa sinh viên hủy đăng ký")
async def delete_class(
    db: Session = Depends(get_database_session)
):
    course_delete = db.query(ClassSchema).filter(ClassSchema.status == 0).all()
    exam_delete = db.query(StudentExamSchema).filter(StudentExamSchema.status == 0).all()
    grade_delete = db.query(GradeSchema).filter(GradeSchema.status == 0).all()
    for course in course_delete:
        db.delete(course)
        db.commit()
    for exam in exam_delete:
        db.delete(exam)
        db.commit()
    for grade in grade_delete:
        db.delete(grade)
        db.commit()
        
        return JSONResponse(status_code=200, content={"message": "Xóa sinh viên thành công!"})
    else:
        return JSONResponse(status_code=400, content={"message": "Error!"})

#Đóng đăng ký học
@router.put("/lock_class",dependencies=[Depends(JWTBearer())], summary="Đóng đăng ký học")
async def lock_class(
    db: Session = Depends(get_database_session),
):
    class_status_exists = db.query(exists().where(ClassSchema.status == 1)).scalar()
    exam_status_exists = db.query(exists().where(StudentExamSchema.status == 1)).scalar()
    grade_status_exists = db.query(exists().where(GradeSchema.status == 1)).scalar()

    if class_status_exists and exam_status_exists and grade_status_exists:
        classid = (db.query
                (
                ClassSchema.classID,
                )
                .select_from(ClassSchema)
                .filter(ClassSchema.status == 1).all()
                )
        examid = (db.query
                (
                StudentExamSchema.id,
                )
                .select_from(StudentExamSchema)
                .filter(StudentExamSchema.status == 1).all()
                )
        gradeid = (db.query
                (
                GradeSchema.gradeID,
                )
                .select_from(GradeSchema)
                .filter(GradeSchema.status == 1).all()
            )  
            
        for classC in classid:
            get_class = db.query(ClassSchema).get(classC)
            get_class.status = 2
        for exam in examid:
            get_exam = db.query(StudentExamSchema).get(exam)
            get_exam.status = 2
        for grade in gradeid:
            get_grade = db.query(GradeSchema).get(grade) 
            get_grade.status = 2
        db.commit()
        db.refresh(get_class)
        db.refresh(get_exam)
        db.refresh(get_grade)
        return JSONResponse(status_code=200, content={"message": "Đã đóng đăng ký học!"})
    else:
        return JSONResponse(status_code=400, content={"message": "Không có dữ liệu!"})
        
#Lấy danh sách lớp
@router.get("/class_by_course/",dependencies=[Depends(JWTBearer())], summary="Lấy danh sách lớp")
def get_class_by_course(
    courseID: int,
    termID: str,
    db: Session = Depends(get_database_session)
):
    classes = (
        db.query(
            ClassSchema.courseID,
            CourseSchema.className,
            ClassSchema.studentID,
            StudentSchema.studentName
        )
        .join(CourseSchema, ClassSchema.courseID == CourseSchema.courseID)
        .join(StudentSchema, ClassSchema.studentID == StudentSchema.studentID)
        .filter(ClassSchema.courseID == courseID, ClassSchema.termID == termID).all()
    )

    result = []
    for get_class in classes:
        result.append(
            {   
                "className": get_class[1],
                "studentID": get_class[2],
                "studentName": get_class[3]
            }
        )
    return {"classCourse": result}

#Lấy TKB sinh viên
@router.get("/class_by_student/",dependencies=[Depends(JWTBearer())], summary="Lấy TKB sinh viên")
def get_courses_with_subject_info(
    studentID: str,
    termID: str,
    db: Session = Depends(get_database_session)
    ):
    classes = (
        db.query(
            StudentSchema.studentID,
            CourseSchema.className,
            CourseSchema.courseDate,
            CourseSchema.courseShiftStart,
            CourseSchema.courseShiftEnd,
            CourseSchema.courseRoom,
            ClassSchema.status
        )
        .join(ClassSchema, CourseSchema.courseID == ClassSchema.courseID)
        .join(StudentSchema, ClassSchema.studentID == StudentSchema.studentID)
        .filter(ClassSchema.studentID == studentID, ClassSchema.termID == termID).all()

    )

    result = []
    for get_class in classes:
        result.append(
            {
                "className": get_class[1],
                "courseDate": get_class[2],
                "courseShiftStart": get_class[3],
                "courseShiftEnd": get_class[4],
                "courseRoom": get_class[5],
                "status":get_class[6]
            }
        )
    return {"schedule": result}

#Lấy TKB sinh viên theo ngày trong tuần
@router.get("/class_by_student/{courseDate}",dependencies=[Depends(JWTBearer())], summary="Lấy TKB sinh viên theo ngày trong tuần")
def get_courses_with_subject_info(
    studentID: str,
    termID: str,
    courseDate = int,
    db: Session = Depends(get_database_session)
    ):
    classes = (
        db.query(
            StudentSchema.studentID,
            CourseSchema.className,
            SubjectSchema.subjectName,
            CourseSchema.courseShiftStart,
            CourseSchema.courseShiftEnd,
            CourseSchema.courseRoom,
            CourseSchema.courseID,
            ClassSchema.status,
        )
        .join(ClassSchema, CourseSchema.courseID == ClassSchema.courseID)
        .join(StudentSchema, ClassSchema.studentID == StudentSchema.studentID)
        .join(SubjectSchema, CourseSchema.subjectID == SubjectSchema.subjectID)
        .filter(ClassSchema.studentID == studentID, ClassSchema.termID == termID, CourseSchema.courseDate == courseDate).all()
    )

    result = []
    for get_class in classes:
        result.append(
            {
                "className": get_class[1],
                "subjectName": get_class[2],
                "courseShiftStart": get_class[3],
                "courseShiftEnd": get_class[4],
                "courseRoom": get_class[5],
                "courseID":get_class[6],
                "status":get_class[7]
            }
        )

    return {"dateSchedule": result}

#Hiện học kỳ hiện tại
@router.get("/current_term/{studentID}", dependencies=[Depends(JWTBearer())], summary="Hiện học kỳ hiện tại")
def get_courses_with_subject_info(studentID: str, db: Session = Depends(get_database_session)):
    today = date.today()
    termDate = db.query(TermSchema.termStart, TermSchema.termEnd).filter(StudentSchema.studentID == studentID,
                                                                         TermSchema.groupID == StudentSchema.group).all()
    lastTerm = termDate[-1]
    start = lastTerm.termStart
    end = lastTerm.termEnd

    terms = (
        db.query(
            TermSchema.id,
            TermSchema.termID,
            TermSchema.termName,
            TermSchema.termStart,
            TermSchema.termEnd
        )
        .filter(StudentSchema.studentID == studentID, StudentSchema.group == TermSchema.groupID,
                TermSchema.termStart == start, TermSchema.termEnd == end, start < today < end).all()
    )

    print(termDate)
    if terms:
        term = terms[0]
        return {
            "id": term[0],
            "termID": term[1],
            "termName": term[2],
            "termStart": term[3],
            "termEnd": term[4]
        }
    else:
        return {"term": None}

#Hiện các môn chưa học
@router.get("/unlearned_subject/{termID}/{studentID}", dependencies=[Depends(JWTBearer())], summary="Hiện các môn chưa học")
def get_unlearned_subject(
    studentID: str,
    termID: str,
    db: Session = Depends(get_database_session)
    ):


    learned = (
        db.query(GradeSchema.subjectID)
        .select_from(GradeSchema)
        .filter(GradeSchema.studentID == studentID,GradeSchema.status==2)
        .distinct()
        .all()
    )
    learned_subject_id = [subject.subjectID for subject in learned]
    print(learned_subject_id)

    unlearnedSubject = (
        db.query(BranchSubjectSchema.subjectID,SubjectSchema.subjectName)
        .select_from(BranchSubjectSchema)
        .join(SubjectSchema,BranchSubjectSchema.subjectID==SubjectSchema.subjectID)
        .join(StudentSchema, StudentSchema.branchID == BranchSubjectSchema.branchID)
        .filter(
            StudentSchema.studentID == studentID,
            ~BranchSubjectSchema.subjectID.in_(learned_subject_id),
            
        )
        .all()
    )

    result = []
    for unlearned in unlearnedSubject:
        result.append(
            {
                "subjectID": unlearned[0],
                "subjectName": unlearned[1]
            }
        )
    return {"unlearnedSubject": result}

