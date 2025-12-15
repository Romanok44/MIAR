import pytest
from uuid import uuid4
from datetime import datetime
from schemas import CartItemCreate, CartItemResponse, CartResponse

def test_cart_item_create_schema():
    product_id = uuid4()
    data = {
        "product_id": product_id,
        "quantity": 2
    }
    schema = CartItemCreate(**data)
    assert schema.product_id == product_id
    assert schema.quantity == 2

def test_cart_item_response_schema():
    item_id = uuid4()
    product_id = uuid4()
    data = {
        "id": item_id,
        "product_id": product_id,
        "name": "Test Product",
        "quantity": 2,
        "price": 100.0,
        "total_price": 200.0,
        "added_at": datetime.utcnow()
    }
    schema = CartItemResponse(**data)
    assert schema.id == item_id
    assert schema.total_price == 200.0