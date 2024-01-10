from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists
import base64
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from datetime import date
from auth.auth_bearer import JWTBearer
from auth.auth_handler import signJWT,decodeJWT,refresh_access_token
from model import UserSchema
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



@router.post("/signup", summary="Đăng ký")
async def create_account(
    db: Session = Depends(get_database_session),
    userName:schema.UserSchema.userName=Form(...),
    userPassword:schema.UserSchema.userPassword=Form(...),
    userRole:schema.UserSchema.userRole=Form(...)
    ):
    user_exists = db.query(exists().where(UserSchema.userName == userName)).scalar()
    if user_exists:
        return JSONResponse(status_code=400, content={"message": "Tài khoản bị trùng"})
    elif len(userPassword)<6:
        return JSONResponse(status_code=400, content={"message": "Mật khẩu tối thiếu là 6 ký tự"})
    userSchema = UserSchema(userName = userName, userPassword=base64.b64encode(userPassword.encode("utf-8")),userRole=userRole)
    db.add(userSchema)
    db.commit()
    db.refresh(userSchema)
    return {
        "data": "Tài khoản đã được tạo thành công!"
    }

@router.post("/login",status_code=status.HTTP_200_OK, summary="Đăng nhập")
async def login(db:Session=Depends(get_database_session),
                userName:schema.UserSchema.userName=Form(...),
                userPassword:schema.UserSchema.userPassword=Form(...)
                ):
    print(userPassword)
    if userPassword == '1':
        return JSONResponse(status_code=400, content={"message": "Sai mật khẩu"})
    password=base64.b64encode(userPassword.encode("utf-8"))
    user_exists = db.query(exists().where(UserSchema.userName == userName)).scalar()
    pass_exists = db.query(exists().where(UserSchema.userPassword==password)).scalar()
    user = db.query(UserSchema).filter(UserSchema.userName == userName).first()
    role_exists = user.userRole if user else None
    # print(password)
    if user_exists==False:
        return JSONResponse(status_code=400, content={"message": "Không có tài khoản"})
    elif pass_exists==False:
        return JSONResponse(status_code=400, content={"message": "Sai mật khẩu"})
    else:
        response_data = {"token": signJWT(userName), "userRole": role_exists}
        return response_data
    
@router.post("/refresh")
async def refresh_token(refresh_token: str):
    return refresh_access_token(refresh_token)

#Đổi mật khẩu
@router.put("/change_password", dependencies=[Depends(JWTBearer())], summary="Đổi mật khẩu")
async def login(db: Session = Depends(get_database_session),
                userID: schema.UserSchema.userName=Form(...),
                userName:schema.UserSchema.userName=Form(...),
                userOldPassword:schema.UserSchema.userPassword=Form(...),
                userNewPassword: str = Form(...),
                userConfirmPassword: str = Form(...)):
    
    Duser = db.query(UserSchema).filter(UserSchema.userName == userName).first()
    user = db.query(UserSchema).get(userID)

    if Duser is None:
        return JSONResponse(status_code=400, content={"message": "Người dùng không hợp lệ!"})

    duserPassword = base64.b64decode(Duser.userPassword + '==').decode("utf-8")
    if userOldPassword != duserPassword:
        return JSONResponse(status_code=400, content={"message": "Sai mật khẩu!"})
    else:
        if userNewPassword == userConfirmPassword:
            if len(userNewPassword) >=6 and len(userConfirmPassword) >= 6:
                newPassword = base64.b64encode(userNewPassword.encode("utf-8"))
                user.userPassword = newPassword
                print(newPassword)
                db.commit()
                db.refresh(user)
                return JSONResponse(status_code=200, content={"message": "Đổi mật khẩu thành công!"})
            else:
                return JSONResponse(status_code=400, content={"message": "Mật khẩu quá ngắn!"})
        else:
            return JSONResponse(status_code=400, content={"message": "Mật khẩu xác nhận không khớp!"})


