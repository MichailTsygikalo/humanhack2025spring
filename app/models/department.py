import sqlalchemy
from sqlalchemy.orm import mapped_column, relationship

from app.core.db import Base

class DepartmentModel(Base):
    __tablename__ = 'department'
    id = mapped_column(sqlalchemy.Integer, primary_key=True)
    name = mapped_column(sqlalchemy.String(256), nullable=False, unique=True)
    s_company = mapped_column(sqlalchemy.Integer, sqlalchemy.ForeignKey("company.id"))
    company = relationship("CompanyModel", back_populates="department")
    employee = relationship("EmployeeModel", back_populates="department")