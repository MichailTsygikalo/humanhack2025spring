import sqlalchemy
from sqlalchemy.orm import mapped_column, relationship

from app.core.db import Base

class RoleModel(Base):
    __tablename__ = 'role'
    id = mapped_column(sqlalchemy.Integer, primary_key=True)
    name = mapped_column(sqlalchemy.String(256), nullable=False, unique=True)
    employee = relationship("EmployeeModel",back_populates="role")