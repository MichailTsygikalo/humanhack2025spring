from pydantic import BaseModel, ConfigDict
from enum import Enum

class Config(BaseModel):
     model_config = ConfigDict(
        arbitrary_types_allowed=True,
        # Другие настройки конфигурации
        # from_attributes=True  # Ранее known_as_orm_mode
    ) 

class DocumentStatus(str, Enum):
    DRAFT = "Черновик"
    PENDING = "На подписании"
    SIGNED = "Подписан"
    REJECTED = "Отклонен"

class UserDocumentSchema(Config):
    doc_name:str | None
    doc_title:str | None
    doc_status:DocumentStatus | None
    sign_status:bool|None
    doc_id:int | None
    employee_id:int|None

class UserDocumentSignSchema(Config):
    doc_name:str | None
    doc_title:str | None
    doc_status:DocumentStatus | None
    sign_status:bool|None
    doc_id:int | None
    employee_id:int|None
    sign:str|None

class EmployeeSign(Config):
    number:int
    employee_id:int

class SendForSignatureSchema(Config):
    employee:list[EmployeeSign]
    doc_id:int

class DocumentSchema(Config):
    name:str
    title:str
    employee_id:int