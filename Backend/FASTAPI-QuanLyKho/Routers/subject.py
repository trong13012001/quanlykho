from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
from model import SubjectSchema, MajorSchema, BranchSubjectSchema,BranchSchema
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

#Tạo môn
@router.post("/create_subject",dependencies=[Depends(JWTBearer())], summary="Tạo môn")
async def create_subject(
    db: Session = Depends(get_database_session),
    subjectID: str = Form(...),
    subjectName: str = Form(...),
    majorID: str = Form(...),
    subjectCredit: str = Form(...)
    ):
    subject_exists = db.query(exists().where(SubjectSchema.subjectID == subjectID)).scalar()
    if subject_exists:
        return {"data": "Trùng mã môn!"}

    subjectSchema = SubjectSchema(subjectID = subjectID, subjectName = subjectName, majorID = majorID, subjectCredit = subjectCredit)
    db.add(subjectSchema)
    db.commit()
    db.refresh(subjectSchema)
    return {
            "data": "Tạo môn học thành công!"
        }

#Sửa môn
@router.put("/update_subject",dependencies=[Depends(JWTBearer())], summary="Sửa môn")
async def update_subject(
    db: Session = Depends(get_database_session),
    subjectID: str = Form(...),
    subjectName: str = Form(...),
    majorID: str = Form(...),
    subjectCredit: str = Form(...)
    ):
    subject_exists = db.query(exists().where(SubjectSchema.subjectID == subjectID)).scalar()

    subject = db.query(SubjectSchema).get(subjectID)
    if subject_exists:
        print(subject)

        subject.subjectName = subjectName
        subject.majorID = majorID
        subject.subjectCredit = subjectCredit

        db.commit()
        db.refresh(subject)

        return {
            "data": "Thông tin môn học đã được cập nhật!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin môn học!"})

#Xóa môn
@router.delete("/delete_subject",dependencies=[Depends(JWTBearer())], summary="Xóa môn")
async def delete_subject(
    db: Session = Depends(get_database_session),
    subjectID: str = Form(...)
):
    subject_exists = db.query(exists().where(SubjectSchema.subjectID == subjectID)).scalar()
    if subject_exists:
        subject = db.query(SubjectSchema).get(subjectID)
        db.delete(subject)
        db.commit()
        return{
         "data": "Xóa môn học thành công!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không tồn tại môn học!"})
    
#Lấy môn
@router.get("/get_subject_by_branch/{branchID}",dependencies=[Depends(JWTBearer())], summary="Lấy môn")
def get_subject_by_branch(branchID: int,
    db: Session = Depends(get_database_session)):

    subjects = (
        db.query(
            SubjectSchema.subjectID,
            SubjectSchema.subjectName,
            SubjectSchema.subjectCredit,
        )
        .join(BranchSubjectSchema, SubjectSchema.subjectID == BranchSubjectSchema.subjectID)
        .filter(BranchSubjectSchema.branchID == branchID)

    )

    result = []
    for subject in subjects:
        result.append(
            {
                "subjectId": subject[0],
                "subjectName": subject[1],
                "credit": subject[2]
            }
        )

    # Return the result as a dictionary
    return {"subject": result}