from fastapi import APIRouter, Depends,status,HTTPException
from fastapi.responses import JSONResponse

from app.core.db import get_session, Session
from app.schema import UserReg
from app.models import UserModel
router = APIRouter()

@router.post('/registration', status_code=status.HTTP_200_OK)
def registr(user: UserReg, session:Session = Depends(get_session)):
    user_model = UserModel(
        email = user.email,
        password = user.password, 
        phone = user.phone
    )
    if user_model.check_user_exists(session=session):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже зарегистрирован"
        )
    new_user = user_model.create_new_user(session=session)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"ans": f"Пользователь зарегистрирован {new_user.email}"}
    )