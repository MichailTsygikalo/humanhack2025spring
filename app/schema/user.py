from pydantic import BaseModel, ConfigDict

class Config(BaseModel):
     model_config = ConfigDict(
        arbitrary_types_allowed=True,
        # Другие настройки конфигурации
        # from_attributes=True  # Ранее known_as_orm_mode
    ) 

class UserReg(Config):
    email:str
    password:str 
    phone:str

class EmployeeSchema(Config):
    id:int
    name:str
    company:str
    department:str|None
    role:str

class AddEmployeeSchema(Config):
    name:str
    company_id:int
    department_id:int
    role_id:int

class CompanyDepartmentsSchema(Config):
    company_name:str
    department_name:str
    company_id:int
    department_id:int

class AllRRoleSchema(Config):
    id:int
    name:str
