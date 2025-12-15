import pytest
from uuid import uuid4
from datetime import datetime
from models import Cart, CartItem

@pytest.fixture
def sample_cart():
    return Cart(
        id=uuid4(),
        user_id=uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def sample_cart_item(sample_cart):
    return CartItem(
        id=uuid4(),
        cart_id=sample_cart.id,
        product_id=uuid4(),
        name="Test Product",
        quantity=2,
        price=100.0,
        added_at=datetime.utcnow()
    )

def test_cart_creation(sample_cart):
    assert sample_cart.id is not None
    assert sample_cart.user_id is not None
    assert sample_cart.created_at is not None

def test_cart_item_creation(sample_cart_item):
    assert sample_cart_item.id is not None
    assert sample_cart_item.cart_id is not None
    assert sample_cart_item.product_id is not None
    assert sample_cart_item.name == "Test Product"
    assert sample_cart_item.quantity == 2
    assert sample_cart_item.price == 100.0