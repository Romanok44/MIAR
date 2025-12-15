import pytest
import requests
from uuid import uuid4

BASE_URL = "http://localhost:8001/api"


@pytest.fixture
def user_id():
    return str(uuid4())


@pytest.fixture
def product_id():
    return "5d0b0c9e-7aa9-4b15-84a9-20111a597ad0"  # Аспирин из мок данных


def test_add_to_cart(user_id, product_id):
    response = requests.post(
        f"{BASE_URL}/cart/items?user_id={user_id}",
        json={"product_id": product_id, "quantity": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == product_id
    assert data["quantity"] == 2
    assert "id" in data


def test_get_cart(user_id, product_id):
    # Сначала добавляем товар
    requests.post(
        f"{BASE_URL}/cart/items?user_id={user_id}",
        json={"product_id": product_id, "quantity": 1}
    )

    # Затем получаем корзину
    response = requests.get(f"{BASE_URL}/cart?user_id={user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert len(data["items"]) > 0
    assert data["total_price"] > 0


def test_remove_from_cart(user_id, product_id):
    # Сначала добавляем товар
    add_response = requests.post(
        f"{BASE_URL}/cart/items?user_id={user_id}",
        json={"product_id": product_id, "quantity": 1}
    )
    item_id = add_response.json()["id"]

    # Затем удаляем
    response = requests.delete(f"{BASE_URL}/cart/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Товар удален из корзины"