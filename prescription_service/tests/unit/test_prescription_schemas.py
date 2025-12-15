import pytest
from uuid import uuid4
from datetime import datetime, date
from schemas import PrescriptionCreate, MedicationCreate, PrescriptionVerify

def test_medication_create_schema():
    product_id = uuid4()
    data = {
        "product_id": product_id,
        "product_name": "Test Med",
        "dosage": "500mg",
        "quantity": 1
    }
    schema = MedicationCreate(**data)
    assert schema.product_id == product_id
    assert schema.product_name == "Test Med"

def test_prescription_create_schema():
    user_id = uuid4()
    data = {
        "user_id": user_id,
        "doctor_name": "Dr. Test",
        "clinic_name": "Test Clinic",
        "issue_date": date.today(),
        "expiry_date": date.today(),
        "medications": [
            {
                "product_id": uuid4(),
                "product_name": "Test Med",
                "dosage": "500mg",
                "quantity": 1
            }
        ]
    }
    schema = PrescriptionCreate(**data)
    assert schema.user_id == user_id
    assert len(schema.medications) == 1