from fastapi import APIRouter

from app.routes.reg import router as reg
from app.routes.doc_api import router as doc
from app.routes.auth import router as au

router = APIRouter()

router.include_router(reg, tags=['Регистрация'])
router.include_router(doc)
router.include_router(au, tags=['Авторизация'])


