from fastapi import APIRouter, Depends, HTTPException, Query
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


# Mock data for products (в реальной системе это был бы отдельный сервис каталога)
PRODUCTS_DATA = {
    "5d0b0c9e-7aa9-4b15-84a9-20111a597ad0": {"name": "Аспирин", "price": 150.00},
    "a1b2c3d4-e5f6-47a8-9b0c-1d2e3f4a5b6c": {"name": "Ношпа", "price": 280.00},
    "b2c3d4e5-f6g7-48b9-9c0d-2e3f4a5b6c7d": {"name": "Парацетамол", "price": 90.00},
    "c3d4e5f6-g7h8-49c0-0d1e-3f4a5b6c7d8e": {"name": "Ибупрофен", "price": 120.00}
}


@router.post("/cart/items", response_model=schemas.CartItemResponse)
def add_to_cart(item: schemas.CartItemCreate, user_id: UUID = Query(...), db: Session = Depends(get_db)):
    """Добавить товар в корзину"""

    # Вложенные функции для бизнес-логики
    def validate_quantity(quantity: int) -> bool:
        """Валидация количества товара"""
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным")
        if quantity > 10:
            raise ValueError("Нельзя добавить более 10 единиц одного товара")
        return True

    def get_product_info(product_id: UUID) -> dict:
        """Получение информации о товаре"""
        product_str = str(product_id)
        if product_str not in PRODUCTS_DATA:
            raise ValueError("Товар не найден в каталоге")
        return PRODUCTS_DATA[product_str]

    def calculate_total_price(price: float, quantity: int) -> float:
        """Расчет общей стоимости"""
        return round(price * quantity, 2)

    # Применяем бизнес-логику
    try:
        validate_quantity(item.quantity)
        product_info = get_product_info(item.product_id)

        # Находим или создаем корзину пользователя
        cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
        if not cart:
            cart = models.Cart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)

        # Проверяем, есть ли уже этот товар в корзине
        existing_item = db.query(models.CartItem).filter(
            models.CartItem.cart_id == cart.id,
            models.CartItem.product_id == item.product_id
        ).first()

        if existing_item:
            # Обновляем количество
            new_quantity = existing_item.quantity + item.quantity
            validate_quantity(new_quantity)
            existing_item.quantity = new_quantity
            cart_item = existing_item
        else:
            # Добавляем новый товар
            cart_item = models.CartItem(
                cart_id=cart.id,
                product_id=item.product_id,
                name=product_info["name"],
                quantity=item.quantity,
                price=product_info["price"]
            )
            db.add(cart_item)

        db.commit()
        db.refresh(cart_item)

        # Формируем ответ
        response = schemas.CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            name=cart_item.name,
            quantity=cart_item.quantity,
            price=cart_item.price,
            total_price=calculate_total_price(cart_item.price, cart_item.quantity),
            added_at=cart_item.added_at
        )

        return response

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/cart/items/{item_id}")
def remove_from_cart(item_id: UUID, db: Session = Depends(get_db)):
    """Удалить товар из корзины"""
    cart_item = db.query(models.CartItem).filter(models.CartItem.id == item_id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Товар не найден в корзине")

    db.delete(cart_item)
    db.commit()

    return {
        "message": "Товар удален из корзины",
        "deleted_item_id": str(item_id)
    }


@router.delete("/cart/clear")
def clear_cart(user_id: UUID = Query(...), db: Session = Depends(get_db)):
    """Очистить корзину"""
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Корзина не найдена")

    # Удаляем все товары из корзины
    db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
    db.commit()

    # Отправляем сообщение о очистке корзины
    asyncio.create_task(rabbitmq.send_cart_cleared_message({
        "user_id": str(user_id),
        "cleared_at": datetime.utcnow().isoformat()
    }))

    return {
        "message": "Корзина очищена",
        "cleared_at": datetime.utcnow()
    }


@router.get("/cart", response_model=schemas.CartResponse)
def get_cart(user_id: UUID = Query(...), db: Session = Depends(get_db)):
    """Просмотреть корзину"""
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if not cart:
        # Возвращаем пустую корзину
        return schemas.CartResponse(user_id=user_id, items=[], total_price=0.0)

    items = []
    total_price = 0.0

    for item in cart.items:
        item_total = item.price * item.quantity
        items.append(schemas.CartItemResponse(
            id=item.id,
            product_id=item.product_id,
            name=item.name,
            quantity=item.quantity,
            price=item.price,
            total_price=item_total,
            added_at=item.added_at
        ))
        total_price += item_total

    return schemas.CartResponse(
        user_id=user_id,
        items=items,
        total_price=round(total_price, 2)
    )