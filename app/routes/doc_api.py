from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
import sqlalchemy
import hashlib
import os

from app.config import BASE_DIR
from app.core.db import get_session
from app.models import UserModel
from app.routes.auth import get_current_user
from app.models.document import DocumentStatus
from app.schema import UserDocumentSchema, UserDocumentSignSchema, SendForSignatureSchema, DocumentSchema, EmployeeSchema, CompanyDepartmentsSchema, AddEmployeeSchema,AllRRoleSchema

UPLOAD_DIR = BASE_DIR / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

@router.get('/all_doc_user', tags=['Документы, составленные пользователем'])
def get_doc_cur_user(current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session))->list[UserDocumentSchema]:
    sql = sqlalchemy.text(
        """
        select d."name" doc_name, d.title doc_title, d.status doc_status, d.s_employee employee_id, d.id doc_id from "document" d
        inner join employee e on e.id = d.s_employee
        inner join "user" u on u.id = e.s_user
        where u.id = :id
        """
    )
    result = session.execute(sql, {"id":current_user.id}).mappings().all()
    documents = [UserDocumentSchema(**row) for row in result]
    return documents

@router.get('/all_sign_doc_user', tags=['Документы, которые пользователь должен подписать или подписал (см статус)'])
def get_doc_sign_cur_user(current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session))->list[UserDocumentSignSchema]:
    sql = sqlalchemy.text(
        """
        SELECT d."name" AS doc_name, 
            d.title AS doc_title, 
            d.status AS doc_status, 
            d.id AS doc_id, 
            ds.s_employee employee_id,
            ds.status sign_status,
            ds.signture sign
        FROM document_signature ds 
        LEFT JOIN "document" d ON d.id = ds.s_document
        INNER JOIN employee e ON e.id = ds.s_employee
        INNER JOIN "user" u ON u.id = e.s_user
        WHERE u.id = :id 
        and
        (ds.status = false  
            AND NOT EXISTS (
            SELECT 1 
            FROM document_signature prev_ds
            WHERE prev_ds.s_document = ds.s_document
            AND prev_ds.number_for_signature < ds.number_for_signature
            AND prev_ds.status = false  
        )or ds.status = true)
        """
    )
    result = session.execute(sql, {"id":current_user.id}).mappings().all()
    documents = [UserDocumentSignSchema(**row) for row in result]
    return documents

@router.post('/generate_signature', tags=['Подписать документ'])
def generate_signature(doc_id:int, employee_id:int,current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session)):
    signature = hashlib.sha256(f'{current_user.phone}-{doc_id}'.encode()).hexdigest()
    sql = sqlalchemy.text(
        """
        SELECT ds.id
        FROM document_signature ds
        WHERE ds.s_employee = :employee_id
        AND ds.s_document = :document_id
        AND ds.status = false
        AND NOT EXISTS (
            SELECT 1
            FROM document_signature prev_ds
            WHERE prev_ds.s_document = ds.s_document
                AND prev_ds.number_for_signature < ds.number_for_signature
                AND prev_ds.status = false
        )
        ORDER BY ds.number_for_signature DESC
        LIMIT 1;
        """
    )
    result = session.execute(sql, {"employee_id":employee_id, "document_id":doc_id}).mappings().first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Документ не может быть подписан"
        )
    
    sql = sqlalchemy.text(
        """
        UPDATE public.document_signature
        SET status=true, signture=:signature
        WHERE id=:id
        """
    )
    
    session.execute(sql, {"signature":signature, "id":result.id})
    session.commit()

    sql = sqlalchemy.text(
        """
        SELECT 
            e.id AS employee_id,
            e.name AS employee_name,
            u.email AS employee_email,
            u.phone AS employee_phone,
            ds.number_for_signature AS signature_order
        FROM 
            document_signature ds
        JOIN 
            employee e ON ds.s_employee = e.id
        JOIN 
            "user" u ON e.s_user = u.id
        WHERE 
            ds.s_document = :document_id
            AND ds.status = false
            AND ds.number_for_signature = (
                SELECT MIN(ds2.number_for_signature)
                FROM document_signature ds2
                WHERE ds2.s_document = ds.s_document
                AND ds2.status = false
            )
        ORDER BY 
            ds.number_for_signature ASC
        LIMIT 1;
        """
    )
    result = session.execute(sql, {"document_id":doc_id}).mappings().first()

    if result is None:
        sql = sqlalchemy.text(
            """
            UPDATE public."document"
            SET  status=:status
            WHERE id=:id
            """
        )
        session.execute(sql, {"status":DocumentStatus.SIGNED,"id":doc_id})
        session.commit() 
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "Документ успешно подписан всеми участниками"}
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Отправлено следующему подписанту"
        }
    )   



@router.post('/reject_signature', tags=['Отклонить подписание'])
def reject_signature(doc_id:int, employee_id:int,current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session)):
    signature = hashlib.sha256(current_user.phone.encode()).hexdigest()
    sql = sqlalchemy.text(
        """
        SELECT ds.id, ds.s_document
        FROM document_signature ds
        WHERE ds.s_employee = :employee_id
        AND ds.s_document = :document_id
        AND ds.status = false
        AND NOT EXISTS (
            SELECT 1
            FROM document_signature prev_ds
            WHERE prev_ds.s_document = ds.s_document
                AND prev_ds.number_for_signature < ds.number_for_signature
                AND prev_ds.status = false
        )
        ORDER BY ds.number_for_signature DESC
        LIMIT 1;
        """
    )
    result = session.execute(sql, {"employee_id":employee_id, "document_id":doc_id}).mappings().first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Документ нельзя отклонить"
        )
    
    id_doc = result.s_document

    sql = sqlalchemy.text(
        """
        UPDATE public."document"
        SET  status=:status
        WHERE id=:id
        """
    )
    session.execute(sql, {"status":DocumentStatus.REJECTED,"id":id_doc})
    session.commit()

    sql = sqlalchemy.text(
        """
        select ds.id from document_signature ds where ds.s_document  = :id 
        """
    )
    result = session.execute(sql, {"id":id_doc}).mappings().all()

    sql = sqlalchemy.text(
        """
        UPDATE public.document_signature
        SET status=false
        WHERE id=:id
        """
    )
    for res in result:
        session.execute(sql, {"id":res.id})
        session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Документ успешно отклонен, все подписи сброшены"
        }
    )
    

@router.post('/send_for_signature', tags=['Отправить на подпись'])
def send_for_signature(schema: SendForSignatureSchema, current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session))->bool:
    employee = schema.employee
    doc_id = schema.doc_id
    sql = sqlalchemy.text(
        """
        INSERT INTO public.document_signature
        (id, status, s_employee, s_document, number_for_signature)
        VALUES(nextval('document_signature_id_seq'::regclass), false, :employee_id,:doc_id, :number)
        """
    )
    for e in employee:
        try:
            session.execute(sql, {"employee_id":e.employee_id,"doc_id":doc_id,"number":e.number})
            session.commit()
        except Exception as ex:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка при добавлении подписанта: {str(ex)}"
            )
    
    sql = sqlalchemy.text(
        """
        UPDATE public."document"
        SET  status=:status
        WHERE id=:id
        """
    )
    session.execute(sql, {"status":DocumentStatus.PENDING,"id":doc_id})
    session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Документ успешно отправлен на подпись"
        }
    )

@router.post('/add_document', tags=['Создать документ'])
def add_document(doc:DocumentSchema,current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session))->int:
    sql = sqlalchemy.text(
        """
        INSERT INTO public."document"
        (id, "name", s_employee, title, status)
        VALUES(nextval('document_id_seq'::regclass), :name, :id, :title, false)
        RETURNING id
        """
    )
    try:
        ob = session.execute(sql, {"name":doc.name, "id":doc.employee_id, "title":doc.title})
        session.commit()
        inserted_id = ob.scalar()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "document_id": inserted_id,
                "message": "Документ успешно создан"
            }
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании документа: {str(e)}"
        )


@router.get('/get_employee',tags=['Получить сотрудников текущего пользователя'])
def get_employee(current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session))->list[EmployeeSchema]: 
    sql = sqlalchemy.text(
        """
        select t.id, t."name", c."name" company, d."name" department, r."name" role 
        from employee t
        left join company c on c.id = t.s_company
        left join department d on d.id = t.s_department
        left join "role" r on r.id = t.s_role
        where t.s_user = :id
        """
    ) 
    result = session.execute(sql, {"id":current_user.id}).mappings().all()
    employees = [dict(row) for row in result]
    return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "employees": employees
            }
    )  

@router.get('/get_all_employee',tags=['Получить всех сотрудников '])
def get_all_employee(current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session))->list[EmployeeSchema]: 
    sql = sqlalchemy.text(
        """
        select distinct t.id, t."name", c."name" company, d."name" department, r."name" role 
        from employee t
        left join company c on c.id = t.s_company
        left join department d on d.id = t.s_department
        left join "role" r on r.id = t.s_role
        """
    ) 
    result = session.execute(sql).mappings().all()
    employees = [dict(row) for row in result]
        
    return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "employees": employees
            }
        )

@router.post('/add_employee',tags=['Добавить сотрудника'])
def add_employee(employee:AddEmployeeSchema, current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session))->bool:
    sql = sqlalchemy.text(
        """
        INSERT INTO public.employee
        (id, "name", s_user, s_role, s_company, s_department)
        VALUES(nextval('employee_id_seq'::regclass), :name, :user_id, :role_id, :company_id, :department_id)
        returning id
        """
    )
    try:
        result = session.execute(sql, {"name":employee.name, "user_id":current_user.id, "role_id":employee.role_id,"company_id":employee.company_id,"department_id":employee.department_id})
        session.commit()
        employee_id = result.scalar()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "employee_id": employee_id,
                "message": "Сотрудник успешно добавлен"
            }
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при добавлении сотрудника: {str(e)}"
        )       


@router.get('/company_departments', tags=['Получить компании и подразделения'])
def get_company_departments(current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session))->list[CompanyDepartmentsSchema]:
    sql = sqlalchemy.text(
        """
        select distinct d."name" department_name, d.id department_id, c."name" company_name, c.id company_id
        from department d 
        left join company c on c.id = d.s_company
        """
    ) 
    result = session.execute(sql).mappings().all()
    departments = [dict(row) for row in result]
        
    return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "departments": departments
                }
        )

@router.post('/add_company', tags=['Добавить компанию'])
def add_company_departments(company_name: str, current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session)):
    sql = sqlalchemy.text(
        """
        INSERT INTO public.company
        (id, "name")
        VALUES(nextval('company_id_seq'::regclass), :namec)
        returning id
        """
    )
    try:
        result = session.execute(sql, {"namec":company_name})
        session.commit()
        
        company_id = result.scalar()
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при добавлении сотрудника: {str(e)}"
        )    
        
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "company_id": company_id,
            "message": "Компания успешно добавлена"
        }
    )


@router.post('/add_departments', tags=['Добавить отдел'])
def add_company_departments(department_name: str, id_company:int, current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session)):
    sql = sqlalchemy.text(
        """
        INSERT INTO public.department
        (id, "name", s_company)
        VALUES(nextval('department_id_seq'::regclass), :name, :id)
        returning id
        """
    )
    result = session.execute(sql, {"name": department_name, "id": id_company})
    session.commit()
    department_id = result.scalar()
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "department_id": department_id,
            "message": "Отдел успешно добавлен"
        }
    )

@router.get('/all_roles', tags=['Получить все роли'])
def all_roles(current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session))->list[AllRRoleSchema]:
    sql = sqlalchemy.text(
        """
        select t.id, t."name" from role t
        """
    ) 
    result = session.execute(sql).mappings().all()
    roles = [dict(row) for row in result]
        
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "roles": roles
        }
    )


@router.post("/upload/")
async def upload_file(doc_id:int,file: UploadFile = File(...),current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session)):
    if not file.filename.endswith(('.doc', '.docx', '.pdf')):
        raise HTTPException(status_code=400, detail="Only .pdf, .doc and .docx files are allowed")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    sql = sqlalchemy.text(
        """
        UPDATE public."document"
        SET filepath=:file_path
        WHERE id=:id;
        """
    )
    session.execute(sql, {"id":doc_id,"file_path":file_path})
    session.commit()
    
    return {"filename": file.filename, "saved_path": file_path}

@router.get("/download/{doc_id}")
async def download_file(doc_id: int, current_user: UserModel = Depends(get_current_user), session:Session = Depends(get_session)): 
    
    sql = sqlalchemy.text(
        """
        select d.filepath from "document" d where d.id = :id
        """
    )
    result = session.execute(sql, {"id":doc_id}).mappings().first()
    
    file_path = result.filepath
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    file_name = os.path.basename(file_path)
    
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/msword"
    )
