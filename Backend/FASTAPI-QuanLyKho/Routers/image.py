from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter,UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
from model import UserSchema,StudentSchema,TeacherSchema,ImageSchema
import schema
from database import SessionLocal, engine
import model
from PIL import Image
from io import BytesIO

router = APIRouter()  
model.Base.metadata.create_all(bind=engine)


def get_database_session():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
model.Base.metadata.create_all(bind=engine)


def get_database_session():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.post("/uploadfile/",dependencies=[Depends(JWTBearer())])
async def create_upload_file(
    user_id: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_database_session)
):
    image_exists = db.query(exists().where(ImageSchema.userName == user_id)).scalar()
    image_db = db.query(ImageSchema).get(user_id)

    if image_exists:
        image_data = await image.read()
        img = Image.open(BytesIO(image_data))
        max_size = (200, 200)
        img.thumbnail(max_size)

        # Create a new image with the resized dimensions
        resized_img = img.resize(img.size)

        # Save the resized image to a buffer
        output_buffer = BytesIO()
        resized_img.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        # Encode the image as Base64
        encoded_image = base64.b64encode(output_buffer.getvalue()).decode("utf-8")

        image_db.image=encoded_image
        db.commit()
        db.refresh(image_db)

        return {"message":"Cập nhật ảnh đại diện thành công"}
    else:
        return JSONResponse(status_code=400, content={"message": "Thông tin sinh viên không có trong dữ liệu"})