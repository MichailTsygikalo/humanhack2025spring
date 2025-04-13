import sqlalchemy
from sqlalchemy.orm import mapped_column, relationship

from app.core.db import Base

class DocumentSignatureModel(Base):
    __tablename__ = 'document_signature'
    id = mapped_column(sqlalchemy.Integer, primary_key=True)
    # name = mapped_column(sqlalchemy.String(256), nullable=False, unique=True)
    status = mapped_column(sqlalchemy.Boolean, default=False)
    signture = mapped_column(sqlalchemy.String(256))

    number_for_signature = mapped_column(sqlalchemy.Integer)

    s_employee = mapped_column(sqlalchemy.Integer, sqlalchemy.ForeignKey("employee.id"))
    employee = relationship("EmployeeModel", back_populates="document_signature")
    s_document = mapped_column(sqlalchemy.Integer, sqlalchemy.ForeignKey("document.id"))
    document = relationship("DocumentModel", back_populates="document_signature")