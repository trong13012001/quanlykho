from fastapi import Depends, FastAPI, Request, Form,status,Header,APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import exists
from sqlalchemy.orm import Session
from model import YearSchema, TermSchema
from database import SessionLocal, engine
import model
from auth.auth_bearer import JWTBearer
from auth.auth_handler import decodeJWT
router = APIRouter()  
model.Base.metadata.create_all(bind=engine)


def get_database_session():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

#Tạo học kỳ
@router.post("/create_term",dependencies=[Depends(JWTBearer())], summary="Tạo học kỳ")
async def create_term(
    db: Session = Depends(get_database_session),
    termID: int = Form(...),
    termName: str = Form(...),
    termStart: str = Form(...),
    termEnd: str = Form(...),
    groupID: int = Form(...),
    yearID: int = Form(...)
):
    term_exists = db.query(exists().where(TermSchema.termID == termID)).scalar()
    year_exists = db.query(exists().where(YearSchema.yearID == yearID)).scalar()
    yearStart = db.query(YearSchema.yearStart).filter(YearSchema.yearID == yearID).first()
    yearEnd = db.query(YearSchema.yearEnd).filter(YearSchema.yearID == yearID).first()
    if term_exists:
        return {"data": "Trùng kỳ học!"}
    elif year_exists and (termStart < yearStart or termEnd > yearEnd):
        return JSONResponse(status_code=400, content={"message": "Thời gian kỳ học không thể nằm ngoài phạm vi thời gian năm học!"})
    elif year_exists:
        termSchema = TermSchema(termID = termID, termName = termName, termStart = termStart, termEnd = termEnd, groupID = groupID, yearID = yearID)
        db.add(termSchema)
        db.commit()
        db.refresh(termSchema)
        return{
            "data": "Tạo kỳ học thành công!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không tồn tại năm học!"})

#Sửa học kỳ
@router.put("/update_term",dependencies=[Depends(JWTBearer())], summary="Sửa học kỳ")
async def create_term(
    db: Session = Depends(get_database_session),
    termID: int = Form(...),
    termName: str = Form(...),
    termStart: str = Form(...),
    termEnd: str = Form(...),
    groupID: int = Form(...),
    yearID: int = Form(...)
):
    term_exists = db.query(exists().where(TermSchema.termID == termID)).scalar()
    year_exists = db.query(exists().where(YearSchema.yearID == yearID)).scalar()
    yearStart = db.query(YearSchema.yearStart).filter(YearSchema.yearID == yearID).first()
    yearEnd = db.query(YearSchema.yearEnd).filter(YearSchema.yearID == yearID).first()
    term = db.query(TermSchema).get(termID)

    if year_exists and (termStart < yearStart or termEnd > yearEnd):
        return JSONResponse(status_code=400, content={"message": "Thời gian kỳ học không thể nằm ngoài phạm vi thời gian năm học!"})
    elif term_exists and year_exists:
        term.termName = termName
        term.termStart = termStart
        term.termEnd = termEnd
        term.groupID = groupID
        term.YearID = yearID

        db.commit()
        db.refresh(term)

        return {
            "data": "Thông tin học kỳ đã được cập nhật!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không có thông tin học kỳ!"})

#Xóa học kỳ
@router.delete("/delete_term",dependencies=[Depends(JWTBearer())], summary="Xóa học kỳ")
async def delete_term(
    db: Session = Depends(get_database_session),
    termID: str = Form(...)
):
    term_exists = db.query(exists().where(TermSchema.termID == termID)).scalar()
    if term_exists:
        term = db.query(TermSchema).get(termID)
        db.delete(term)
        db.commit()
        return{
         "data": "Xóa học kỳ thành công!"
        }
    else:
        return JSONResponse(status_code=400, content={"message": "Không tồn tại học kỳ!"})

#Lấy thông tin học kỳ   
@router.get("/term_info/{termID}",dependencies=[Depends(JWTBearer())], summary="Lấy thông tin học kỳ")
def get_term_info(
    termID = str,
    db: Session = Depends(get_database_session)
    ):
    term = (
        db.query(
            TermSchema.termName,
            TermSchema.termStart,
            TermSchema.termEnd,
            TermSchema.groupID,
            TermSchema.yearID
        )
        .filter(TermSchema.termID == termID)
        .first()
    )

    if term is None:
        return {"term": {}}
    
    result = {
                "termName": term[0],
                "termStart": term[1],
                "termEnd": term[2],
                "groupID": term[3],
                "yearID": term[4]
            }

    return {"term": result}

#Lấy thông tin học kỳ trong năm học
@router.get("/term_info_by_year/{yearID}",dependencies=[Depends(JWTBearer())], summary="Lấy thông tin học kỳ trong năm học")
def get_term_info_by_year(
    yearID = int,
    db: Session = Depends(get_database_session)
    ):
    get_term = (
        db.query(
            TermSchema.termID,
            TermSchema.termName,
            TermSchema.termStart,
            TermSchema.termEnd,
            TermSchema.groupID
        )
        .join(YearSchema, TermSchema.yearID == YearSchema.yearID)
        .filter(TermSchema.yearID == yearID).all()
    )

    result = []
    for term in get_term:
        result.append(
            {
                "termID": term[0],
                "termName": term[1],
                "termStart": term[2],
                "termEnd": term[3],
                "groupID": term[4]
            }
        )

    return {"term": result}

#Lấy danh sách học kỳ
@router.get("/term_list/",dependencies=[Depends(JWTBearer())], summary="Lấy danh sách học kỳ")
def get_term_list(
    db: Session = Depends(get_database_session)
    ):
    get_term = (db.query(TermSchema.id,
                         TermSchema.termID,
                         TermSchema.termName,
                         TermSchema.groupID,
                         TermSchema.yearID).all())

    result = []
    for term in get_term:
        result.append(
            {   "id":term[0],
                "termID": term[1],
                "termName": term[2],
                "groupID": term[3],
                "yearID": term[4],
            }
        )

    return {"term": result}