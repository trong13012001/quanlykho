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
from model import ProductSchema


router = APIRouter()  
model.Base.metadata.create_all(bind=engine)


def get_database_session():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
#Tạo sản phẩm
@router.post("/create_product",dependencies=[Depends(JWTBearer())], summary="Tạo sản phẩm")
async def create_product(
    db: Session = Depends(get_database_session),
    productId: str = Form(...),
    supplierId: str = Form(...),
    productName: str = Form(...),
    categoryId: str = Form(...),
    brand:str = Form(...),
    serial:str = Form(...),
    description:str = Form(...),
    quantity: int = Form(...),
    unitPrice: float = Form(...),
):
    product_exists = db.query(exists().where(ProductSchema.productId == productId)).scalar()
    if product_exists:
        return {"data": "Sản phẩm đã tồn tại!"}
    productSchema = ProductSchema(productId = productId,supplierId = supplierId, productName = productName,categoryId=categoryId,brand=brand,serial=serial,description=description,quantity=quantity,unitPrice=unitPrice,hasBeenDeleted=0)
    db.add(productSchema)
    db.commit()
    db.refresh(productSchema)
    return {
        "data:" "Tạo sản phẩm thành công!"
    }

#Sửa thông tin sản phẩm
@router.put("/update_product",dependencies=[Depends(JWTBearer())], summary="Sửa sản phẩm")
async def update_product(
    db: Session = Depends(get_database_session),
    productId: str = Form(...),
    supplierId: str = Form(...),
    productName: str = Form(...),
    categoryId: str = Form(...),
    brand:str = Form(...),
    serial:str = Form(...),
    description:str = Form(...),
    quantity: int = Form(...),
    unitPrice: float = Form(...),
    hasBeenDeleted:int=Form(...)
):
    product_exists = db.query(exists().where(ProductSchema.productId == productId)).scalar()
    product = db.query(ProductSchema).get(productId)
    if product_exists:
        print(product)
        product.productName = productName
        product.supplierId = supplierId
        product.categoryId = categoryId
        product.brand = brand
        product.serial = serial
        product.description = description
        product.quantity = quantity
        product.unitPrice = unitPrice
        db.commit()
        db.refresh(product)
        return {
            "data": "Thông tin sản phẩm đã được cập nhật!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin sản phẩm!"})

#Xóa sản phẩm
@router.delete("/delete_product",dependencies=[Depends(JWTBearer())], summary="Xóa sản phẩm")
async def delete_product(
    db: Session = Depends(get_database_session),
    Id: int = Form(...)
):
    product_exists = db.query(exists().where(ProductSchema.Id == Id)).scalar()
    if product_exists:
        product = db.query(ProductSchema).get(Id)
        product.hasBeenDeleted=1
        # db.delete(product)
        db.commit()
        db.refresh(product)

        return{
         "data": "Xóa sản phẩm thành công!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không tồn tại sản phẩm!"})

#Lấy sản phẩm theo mã sản phẩm
@router.get("/product/{productId}", summary="Lấy sản phẩm theo mã")
def get_courses_with_subject_info(
    db: Session = Depends(get_database_session),
    productId=str
):
    products = (
    db.query(ProductSchema)  # Specify the model (ProductSchema) to query
    .filter(ProductSchema.productId == productId)
    .all()
    )
    print(products)
    result = []
    for product in products:
        result.append(
            {   
              product
            }
        )
    return {"data": result}

#Lấy tất cả sản phẩm
@router.get("/products", summary="Lấy tất cả sản phẩm")
def get_products(
    db: Session = Depends(get_database_session),
):
    products = (
    db.query(ProductSchema)  # Specify the model (ProductSchema) to query
    .all()
    )
    print(products)
    result = []
    for product in products:
        result.append(
            {   
              product
            }
        )
    return {"data": result}

#Lấy tất cả sản phẩm còn trong kho
@router.get("/products/all", summary="Lấy sản phẩm theo mã")
def get_all_products(
    db: Session = Depends(get_database_session),
):
    products = (
    db.query(ProductSchema) 
    .filter(ProductSchema.quantity>0,ProductSchema.hasBeenDeleted == 0)
    .all()
    )
    print(products)
    result = []
    for product in products:
        result.append(
            {   
              product
            }
        )
    return {"data": result}
#Lấy tất cả sản phẩm theo hãng
@router.get("/products/all/brand", summary="Lấy sản phẩm theo hãng")
def get_all_products_with_category(
    brand: str = Query(None, description="Filter products by brand"),
    db: Session = Depends(get_database_session),
):
    query = (
        db.query(ProductSchema)
    )

    if brand:
        query = query.filter(ProductSchema.brand == brand)

    products = query.all()
    result = []
    for product in products:
        result.append(
            {   
              product
            }
        )
    return {"data": result}

#Lấy tất cả sản phẩm theo hãng và còn hàng (chạy không lọc ra theo hãng)
@router.get("/products/all/brand/instock", summary="Lấy sản phẩm theo hãng và còn hàng")
def get_all_products_with_category(
    brand: str = Query(None, description="Filter products by brand"),
    db: Session = Depends(get_database_session),
):
    query = (
        db.query(ProductSchema)
        .filter(ProductSchema.quantity > 0, ProductSchema.hasBeenDeleted == 0)
    )

    if brand:
        query = query.filter(ProductSchema.brand == brand)

    products = query.all()
    result = []
    for product in products:
        result.append(
            {   
              product
            }
        )
    return {"data": result}

#Lấy tất cả sản phẩm theo loại
@router.get("/products/all/category", summary="Lấy sản phẩm theo loại")
def get_all_products_with_category(
    categoryId: str = Query(None, description="Lọc sản phẩm theo loại"),
    db: Session = Depends(get_database_session),
):
    query = (
        db.query(ProductSchema)
    )

    if categoryId:
        query = query.filter(ProductSchema.categoryId == categoryId)

    products = query.all()
    result = []
    for product in products:
        result.append(
            {   
              product
            }
        )
    return {"data": result}

#Lấy tất cả sản phẩm thuộc loại được chọn và còn hàng
@router.get("/products/all/category/instock", summary="Lấy sản phẩm theo loại và còn hàng")
def get_all_products_with_category(
    categoryId: str = Query(None, description="Lọc sản phẩm theo loại và còn hàng"),
    db: Session = Depends(get_database_session),
):
    query = (
        db.query(ProductSchema)
        .filter(ProductSchema.quantity > 0, ProductSchema.hasBeenDeleted == 0)
    )
#dadad
    if categoryId:
        query = query.filter(ProductSchema.categoryId == categoryId)

    products = query.all()
    result = []
    for product in products:
        result.append(
            {   
              product
            }
        )
    return {"data": result}
