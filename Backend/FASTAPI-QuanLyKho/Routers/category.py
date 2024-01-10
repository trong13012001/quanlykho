from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
from model import CategorySchema
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

#Thêm loại
@router.post("/create_category",dependencies=[Depends(JWTBearer())], summary="Tạo loại sản phẩm")
async def create_category(
    db: Session = Depends(get_database_session),
    categoryName: str = Form(...),
):
    category_exists = db.query(exists().where(CategorySchema.categoryName == categoryName)).scalar()
    if category_exists:
        return {"data": "Loại sản phẩm đã tồn tại!"}
    categorySchema = CategorySchema(categoryName = categoryName)
    db.add(categorySchema)
    db.commit()
    db.refresh(categorySchema)
    return {
        "data:" "Tạo loại sản phẩm thành công!"
    }

# Sủa loại sản phẩm
@router.post("/update_category",dependencies=[Depends(JWTBearer())], summary="Sửa loại sản phẩm")
async def update_category(
    db: Session = Depends(get_database_session),
    categoryName: str = Form(...),
):
    category_exists = db.query(exists().where(CategorySchema.categoryName == categoryName)).scalar()
    category = db.query(CategorySchema).get(categoryName)
    if category_exists:
        print(category)
        category.categoryName = categoryName
        db.commit()
        db.refresh(category)
        return {
            "data": "Thông tin sản phẩm đã được cập nhật!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin loại sản phẩm!"})

#Xóa loại sản phẩm
@router.delete("/delete_category",dependencies=[Depends(JWTBearer())], summary="Xóa loại sản phẩm")
async def delete_category(
    db: Session = Depends(get_database_session),
    Id: int = Form(...)
):
    category_exists = db.query(exists().where(CategorySchema.Id == Id)).scalar()
    if category_exists:
        category = db.query(CategorySchema).get(Id)
        category.hasBeenDeleted=1
        # db.delete(product)
        db.commit()
        db.refresh(category)

        return{
         "data": "Xóa loại sản phẩm thành công!" 
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không tồn tại loại sản phẩm!"})
    
#Lấy tất cả loại sản phẩm
@router.get("/category", summary="Lấy tất cả loại sản phẩm")
def get_category(
    db: Session = Depends(get_database_session),
):
    category = (
    db.query(CategorySchema)
    .all()
    )
    print(category)
    result = []
    for category in category:
        result.append(
            {   
              category
            }
        )
    return {"data": result}

