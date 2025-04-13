import sqlalchemy
from sqlalchemy.orm import mapped_column, relationship

from app.core.db import Base

class CompanyModel(Base):
    __tablename__ = 'company'
    id = mapped_column(sqlalchemy.Integer, primary_key=True)
    name = mapped_column(sqlalchemy.String(256), nullable=False, unique=True)
    department = relationship("DepartmentModel", back_populates="company")
    employee = relationship("EmployeeModel", back_populates="company")