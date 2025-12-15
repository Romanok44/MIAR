from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
import asyncio
from . import models, schemas, database, rabbitmq

router = APIRouter()


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/prescriptions", response_model=schemas.PrescriptionUploadResponse)
async def upload_prescription(prescription: schemas.PrescriptionCreate, db: Session = Depends(get_db)):
    """Загрузить рецепт"""

    # Вложенные функции для валидации
    def validate_dates(issue_date, expiry_date):
        """Валидация дат рецепта"""
        if issue_date > datetime.now().date():
            raise ValueError("Дата выписки не может быть в будущем")
        if expiry_date <= issue_date:
            raise ValueError("Срок действия должен быть после даты выписки")
        if expiry_date < datetime.now().date():
            raise ValueError("Рецепт уже просрочен")

    def validate_medications(medications):
        """Валидация списка лекарств"""
        if not medications:
            raise ValueError("Рецепт должен содержать хотя бы одно лекарство")

        for med in medications:
            if med.quantity <= 0:
                raise ValueError("Количество лекарства должно быть положительным")
            if not med.product_name.strip():
                raise ValueError("Название лекарства не может быть пустым")

    def validate_doctor_info(doctor_name, clinic_name):
        """Валидация информации о враче"""
        if not doctor_name.strip():
            raise ValueError("ФИО врача не может быть пустым")
        if not clinic_name.strip():
            raise ValueError("Название клиники не может быть пустым")

    # Применяем валидацию
    try:
        validate_dates(prescription.issue_date, prescription.expiry_date)
        validate_medications(prescription.medications)
        validate_doctor_info(prescription.doctor_name, prescription.clinic_name)

        # Создаем рецепт
        new_prescription = models.Prescription(
            user_id=prescription.user_id,
            doctor_name=prescription.doctor_name,
            clinic_name=prescription.clinic_name,
            issue_date=prescription.issue_date,
            expiry_date=prescription.expiry_date,
            medications=[med.dict() for med in prescription.medications],
            image_url=prescription.image_url
        )

        db.add(new_prescription)
        db.commit()
        db.refresh(new_prescription)

        # Отправляем сообщение о загрузке рецепта
        asyncio.create_task(rabbitmq.send_prescription_uploaded_message({
            "prescription_id": str(new_prescription.id),
            "user_id": str(prescription.user_id),
            "doctor_name": prescription.doctor_name,
            "uploaded_at": new_prescription.created_at.isoformat()
        }))

        return schemas.PrescriptionUploadResponse(
            id=new_prescription.id,
            user_id=new_prescription.user_id,
            status=new_prescription.status,
            created_at=new_prescription.created_at
        )

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/prescriptions/{prescription_id}/verify", response_model=schemas.PrescriptionVerifyResponse)
def verify_prescription(prescription_id: UUID, verify_data: schemas.PrescriptionVerify, db: Session = Depends(get_db)):
    """Проверить рецепт (подтвердить/отклонить)"""

    prescription = db.query(models.Prescription).filter(models.Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    # Вложенные функции для бизнес-логики проверки
    def validate_prescription_status(current_status):
        """Проверка текущего статуса рецепта"""
        if current_status != models.PrescriptionStatus.PENDING:
            raise ValueError("Рецепт уже был проверен")

    def check_expiry(expiry_date):
        """Проверка срока действия"""
        if expiry_date < datetime.now().date():
            raise ValueError("Рецепт просрочен и не может быть подтвержден")

    def validate_verifier(verified_by):
        """Валидация проверяющего (в реальной системе проверялись бы права)"""
        if not verified_by:
            raise ValueError("Не указан проверяющий")

    # Применяем бизнес-логику
    try:
        validate_prescription_status(prescription.status)
        check_expiry(prescription.expiry_date)
        validate_verifier(verify_data.verified_by)

        # Обновляем рецепт
        prescription.status = verify_data.status
        prescription.verified_by = verify_data.verified_by
        prescription.verified_at = datetime.utcnow()
        prescription.notes = verify_data.notes
        prescription.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(prescription)

        message = "Рецепт подтвержден" if verify_data.status == models.PrescriptionStatus.APPROVED else "Рецепт отклонен"

        return schemas.PrescriptionVerifyResponse(
            id=prescription.id,
            status=prescription.status,
            verified_by=prescription.verified_by,
            verified_at=prescription.verified_at,
            notes=prescription.notes,
            message=message
        )

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/prescriptions/{prescription_id}", response_model=schemas.PrescriptionResponse)
def get_prescription(prescription_id: UUID, db: Session = Depends(get_db)):
    """Получить рецепт по ID"""
    prescription = db.query(models.Prescription).filter(models.Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    # Преобразуем JSON medications в список объектов
    medications = [
        schemas.MedicationResponse(**med) for med in prescription.medications
    ]

    return schemas.PrescriptionResponse(
        id=prescription.id,
        user_id=prescription.user_id,
        doctor_name=prescription.doctor_name,
        clinic_name=prescription.clinic_name,
        issue_date=prescription.issue_date,
        expiry_date=prescription.expiry_date,
        medications=medications,
        image_url=prescription.image_url,
        status=prescription.status,
        verified_by=prescription.verified_by,
        verified_at=prescription.verified_at,
        notes=prescription.notes,
        created_at=prescription.created_at
    )