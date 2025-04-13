import sqlalchemy
from sqlalchemy.orm import mapped_column, relationship

from app.core.db import Base

class EmployeeModel(Base):
    __tablename__ = 'employee'
    id = mapped_column(sqlalchemy.Integer, primary_key=True)
    name = mapped_column(sqlalchemy.String(256), nullable=False, unique=True)
    s_user = mapped_column(sqlalchemy.Integer, sqlalchemy.ForeignKey("user.id"))
    user = relationship("UserModel", back_populates="employee")
    s_role = mapped_column(sqlalchemy.Integer, sqlalchemy.ForeignKey("role.id"))
    role = relationship("RoleModel", back_populates="employee")
    s_company = mapped_column(sqlalchemy.Integer, sqlalchemy.ForeignKey("company.id"))
    company = relationship("CompanyModel", back_populates="employee")
    s_department = mapped_column(sqlalchemy.Integer, sqlalchemy.ForeignKey("department.id"))
    department = relationship("DepartmentModel", back_populates="employee")

    document = relationship("DocumentModel", back_populates="employee")
    document_signature = relationship("DocumentSignatureModel", back_populates="employee")