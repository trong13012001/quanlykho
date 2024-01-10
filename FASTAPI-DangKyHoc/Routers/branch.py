from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
from model import BranchSchema, MajorSchema
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

#Tạo ngành
@router.post("/create_branch",dependencies=[Depends(JWTBearer())], summary="Tạo ngành")
async def create_branch(
    db: Session = Depends(get_database_session),
    branchID: str = Form(...),
    branchName: str = Form(...),
    majorID: str = Form(...),
    groupEnd:int = Form(...)
):
    branch_exists = db.query(exists().where(BranchSchema.branchID == branchID)).scalar()
    major_non_exists = db.query(exists().where(MajorSchema.majorID != majorID)).scalar()

    if branch_exists:
        return {"data": "Trùng mã ngành!"}
    elif major_non_exists:
        return {"data": "Không tìm thấy khoa!"}
    elif (groupEnd > 3 or groupEnd < 1):
        return {"data": "Nhóm không tồn tại!"}
    branchSchema = BranchSchema(branchID = branchID, branchName = branchName, majorID = majorID, groupEnd = groupEnd)
    db.add(branchSchema)
    db.commit()
    db.refresh(branchSchema)
    return {
        "data:" "Tạo chuyên ngành thành công!"
    }

#Sửa ngành
@router.put("/update_branch",dependencies=[Depends(JWTBearer())], summary="Sửa ngành")
async def update_branch(
    db: Session = Depends(get_database_session),
    branchID: str = Form(...),
    branchName: str = Form(...),
    majorID: str = Form(...),
    groupEnd: int = Form(...)
):
    branch_exists = db.query(exists().where(BranchSchema.branchID == branchID)).scalar()
    major_non_exists = db.query(exists().where(MajorSchema.majorID != majorID)).scalar()
    branch = db.query(BranchSchema).get(branchID)
    if branch_exists:
        print(branch)
        if major_non_exists:
            return {"data": "Không tìm thấy khoa!"}
        elif (groupEnd > 3 or groupEnd < 1):
            return {"data": "Nhóm không tồn tại!"}
        branch.branchName = branchName
        branch.majorID = majorID
        branch.groupEnd = groupEnd
        db.commit()
        db.refresh(branch)
        return {
            "data": "Thông tin chuyên ngành đã được cập nhật!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin chuyên ngành!"})

#Xóa ngành
@router.delete("/delete_branch",dependencies=[Depends(JWTBearer())], summary="Xóa ngành")
async def delete_branch(
    db: Session = Depends(get_database_session),
    branchID: str = Form(...)
):
    branch_exists = db.query(exists().where(BranchSchema.branchID == branchID)).scalar()
    if branch_exists:
        branch = db.query(BranchSchema).get(branchID)
        db.delete(branch)
        db.commit()
        return{
         "data": "Xóa chuyên ngành thành công!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không tồn tại chuyên ngành!"})