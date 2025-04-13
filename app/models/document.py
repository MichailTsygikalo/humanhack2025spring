import sqlalchemy
from sqlalchemy.orm import mapped_column, relationship
from enum import Enum

from app.core.db import Base

class DocumentStatus(str, Enum):
    DRAFT = "Черновик"
    PENDING = "На подписании"
    SIGNED = "Подписан"
    REJECTED = "Отклонен"

class DocumentModel(Base):
    __tablename__ = 'document'
    id = mapped_column(sqlalchemy.Integer, primary_key=True)
    name = mapped_column(sqlalchemy.String(256), nullable=False, unique=True)
    s_employee = mapped_column(sqlalchemy.Integer, sqlalchemy.ForeignKey("employee.id"))
    employee = relationship("EmployeeModel", back_populates="document")
    title = mapped_column(sqlalchemy.String(256))
    status = mapped_column(sqlalchemy.String(50), default=DocumentStatus.DRAFT)
    filepath = mapped_column(sqlalchemy.String(256))

    document_signature = relationship("DocumentSignatureModel", back_populates="document")