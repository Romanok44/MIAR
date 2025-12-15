import pytest
from uuid import uuid4
from datetime import datetime
from models import Prescription, PrescriptionStatus

@pytest.fixture
def sample_prescription():
    return Prescription(
        id=uuid4(),
        user_id=uuid4(),
        doctor_name="Dr. Test",
        clinic_name="Test Clinic",
        issue_date=datetime.utcnow(),
        expiry_date=datetime.utcnow(),
        medications=[{
            "product_id": str(uuid4()),
            "product_name": "Test Medication",
            "dosage": "500mg",
            "quantity": 1
        }],
        status=PrescriptionStatus.PENDING
    )

def test_prescription_creation(sample_prescription):
    assert sample_prescription.id is not None
    assert sample_prescription.doctor_name == "Dr. Test"
    assert sample_prescription.status == PrescriptionStatus.PENDING
    assert len(sample_prescription.medications) == 1