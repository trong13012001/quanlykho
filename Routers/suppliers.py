from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
import schema
from database import SessionLocal, engine
import model
from model import SuppliersSchema


router = APIRouter()  
model.Base.metadata.create_all(bind=engine)


def get_database_session():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
#Tạo nhà cung cấp
@router.post("/create_supplier",dependencies=[Depends(JWTBearer())], summary="Tạo nhà cung cấp")
async def create_suppiler(
    db: Session = Depends(get_database_session),
    _supplierId: int = Form(...),
    supplierName: str = Form(...),
    contactPhone: str = Form(...),
    contactEmail: str = Form(...),
):
    supplier_exists = db.query(exists().where(SuppliersSchema._supplierId == _supplierId)).scalar()
    if supplier_exists:
        return {"data": "Nhà cung cấp đã tồn tại!"}
    supplierSchema = SuppliersSchema(_supplierId = _supplierId, supplierName = supplierName, contactPhone = contactPhone, contactEmail =contactEmail)
    db.add(supplierSchema)
    db.commit()
    db.refresh(supplierSchema)
    return {
        "data:" "Tạo nhà cung cấp thành công!"
    }

#Sửa thông tin nhà cung cấp
@router.put("/update_suppiler",dependencies=[Depends(JWTBearer())], summary="Sửa thông tin nhà cung cấp")
async def update_supplier(
    db: Session = Depends(get_database_session),
    _supplierId: int = Form(...),
    supplierName: str = Form(...),
    contactPhone: str = Form(...),
    contactEmail: str = Form(...),
):
    supplier_exists = db.query(exists().where(SuppliersSchema._supplierId == _supplierId)).scalar()
    supplier = db.query(SuppliersSchema).get(_supplierId)
    if supplier_exists:
        print(supplier)
        supplier.supplierName = supplierName
        supplier.contactPhone = contactPhone
        supplier.contactEmail = contactEmail
        db.commit()
        db.refresh(supplier)
        return {
            "data": "Thông tin nhà cung cấp đã được cập nhật!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin nhà cung cấp!"})

#Xóa nhà cung cấp
@router.delete("/delete_supplier",dependencies=[Depends(JWTBearer())], summary="Xóa nhà cung cấp")
async def delete_supplier(
    db: Session = Depends(get_database_session),
    _supplierId: int = Form(...)
):
    supplier_exists = db.query(exists().where(SuppliersSchema._supplierId == _supplierId)).scalar()
    if supplier_exists:
        supplier = db.query(SuppliersSchema).get(_supplierId)
        supplier.hasBeenDeleted=1
        # db.delete(product)
        db.commit()
        db.refresh(supplier)

        return{
         "data": "Xóa nhà cung cấp thành công!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không tồn tại nhà cung cấp!"})
    
#Lấy thông tin tất cả các nhà cung cấp
@router.get("/suppliers", summary="Lấy tất cả thông tin nhà cung cấp")
def get_supplier(
    db: Session = Depends(get_database_session),
):
    suppliers = (
    db.query(SuppliersSchema)
    .all()
    )
    print(suppliers)
    result = []
    for supplier in suppliers:
        result.append(
            {   
              supplier
            }
        )
    return {"data": result}