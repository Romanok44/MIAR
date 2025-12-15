from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import List, Optional
from enum import Enum


class PrescriptionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MedicationCreate(BaseModel):
    product_id: UUID
    product_name: str
    dosage: str
    quantity: int


class PrescriptionCreate(BaseModel):
    user_id: UUID
    doctor_name: str
    clinic_name: str
    issue_date: date
    expiry_date: date
    medications: List[MedicationCreate]
    image_url: Optional[str] = None


class PrescriptionVerify(BaseModel):
    status: PrescriptionStatus
    verified_by: UUID
    notes: Optional[str] = None


class MedicationResponse(BaseModel):
    product_id: UUID
    product_name: str
    dosage: str
    quantity: int

    class Config:
        from_attributes = True


class PrescriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    doctor_name: str
    clinic_name: str
    issue_date: datetime
    expiry_date: datetime
    medications: List[MedicationResponse]
    image_url: Optional[str]
    status: PrescriptionStatus
    verified_by: Optional[UUID]
    verified_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PrescriptionUploadResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: PrescriptionStatus
    created_at: datetime
    message: str = "Рецепт успешно загружен"


class PrescriptionVerifyResponse(BaseModel):
    id: UUID
    status: PrescriptionStatus
    verified_by: UUID
    verified_at: datetime
    notes: Optional[str]
    message: str