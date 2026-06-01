from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=List[schemas.EmployeeOut])
async def list_employees(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    hire_date_after: Optional[date] = None,
    hire_date_before: Optional[date] = None,
    state: Optional[str] = None,
    language: Optional[str] = None,
    specialty: Optional[str] = None,
    sort_by: Optional[str] = None,
    order: str = "asc",
    db: AsyncSession = Depends(get_db),
):
    return await crud.filter_employees(
        db,
        skip=skip,
        limit=limit,
        role=role,
        hire_date_after=hire_date_after,
        hire_date_before=hire_date_before,
        state=state,
        language=language,
        specialty=specialty,
        sort_by=sort_by,
        order=order,
    )


@router.get("/{employee_id}", response_model=schemas.EmployeeDetailOut)
async def get_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    emp = await crud.get_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.get("/by-employee-id/{employee_id}", response_model=schemas.EmployeeDetailOut)
async def get_employee_by_employee_id(employee_id: str, db: AsyncSession = Depends(get_db)):
    emp = await crud.get_employee_by_employee_id(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.get("/by-name/{name}", response_model=schemas.EmployeeDetailOut)
async def get_employee_by_name(name: str, db: AsyncSession = Depends(get_db)):
    emp = await crud.get_employee_by_name(db, name)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.get("/search/", response_model=List[schemas.EmployeeOut])
async def search_employees(q: str, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.search_employees(db, q, skip=skip, limit=limit)


@router.post("/", response_model=schemas.EmployeeOut, status_code=201)
async def create_employee(payload: schemas.EmployeeCreate, db: AsyncSession = Depends(get_db)):
    emp = models.Employee(
        employee_id=payload.employee_id,
        name=payload.name,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        role=payload.role,
        email=payload.email,
        phone=payload.phone,
        hire_date=payload.hire_date,
        salary_usd=payload.salary_usd,
        notes=payload.notes,
    )
    await crud.create(db, emp)
    if payload.address:
        db.add(
            models.EmployeeAddress(
                employee_id=emp.id,
                street=payload.address.street,
                city=payload.address.city,
                state=payload.address.state,
                zip=payload.address.zip,
                country=payload.address.country,
            )
        )
    for lang in payload.languages:
        db.add(models.EmployeeLanguage(employee_id=emp.id, language=lang))
    for spec in payload.specialties:
        db.add(models.EmployeeSpecialty(employee_id=emp.id, specialty=spec))
    if payload.emergency_contact:
        db.add(
            models.EmployeeEmergencyContact(
                employee_id=emp.id,
                name=payload.emergency_contact.name,
                relation=payload.emergency_contact.relation,
                phone=payload.emergency_contact.phone,
            )
        )
    await db.commit()
    await db.refresh(emp)
    return emp


@router.put("/{employee_id}", response_model=schemas.EmployeeOut)
async def update_employee(
    employee_id: int, payload: schemas.EmployeeUpdate, db: AsyncSession = Depends(get_db)
):
    emp = await crud.get_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    update_data = payload.model_dump(exclude_unset=True)
    return await crud.update_employee(db, emp, update_data)


@router.delete("/{employee_id}", status_code=204)
async def delete_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    emp = await crud.get_by_id(db, models.Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    await crud.delete(db, emp)
