import pytest
import requests
from uuid import uuid4
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8002/api"


@pytest.fixture
def user_id():
    return str(uuid4())


@pytest.fixture
def prescription_data(user_id):
    return {
        "user_id": user_id,
        "doctor_name": "Доктор Иванов",
        "clinic_name": "Городская поликлиника",
        "issue_date": str(date.today()),
        "expiry_date": str(date.today() + timedelta(days=90)),
        "medications": [
            {
                "product_id": "5d0b0c9e-7aa9-4b15-84a9-20111a597ad0",
                "product_name": "Аспирин",
                "dosage": "500 мг",
                "quantity": 1
            }
        ],
        "image_url": "https://example.com/prescription.jpg"
    }


def test_upload_prescription(prescription_data):
    response = requests.post(f"{BASE_URL}/prescriptions", json=prescription_data)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == prescription_data["user_id"]
    assert data["status"] == "pending"
    assert "id" in data
    return data["id"]


def test_get_prescription(prescription_data):
    # Сначала загружаем рецепт
    prescription_id = test_upload_prescription(prescription_data)

    # Затем получаем его
    response = requests.get(f"{BASE_URL}/prescriptions/{prescription_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == prescription_id
    assert data["doctor_name"] == prescription_data["doctor_name"]
    assert len(data["medications"]) == 1