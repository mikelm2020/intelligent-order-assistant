from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status import OrderStatus


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        customer_id: int,
        status: OrderStatus = OrderStatus.PENDING,
    ) -> Order:
        order = Order(
            customer_id=customer_id,
            status=status.value,
        )

        self.session.add(order)
        await self.session.flush()

        return order

    async def add_item(
        self,
        order_id: int,
        product_id: int,
        quantity: int,
        unit_price: Decimal,
        subtotal: Decimal,
    ) -> OrderItem:
        item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        )

        self.session.add(item)
        await self.session.flush()

        return item

    async def get_by_id(
        self,
        order_id: int,
    ) -> Order | None:
        statement = (
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )

        result = await self.session.scalars(statement)

        return result.first()

    async def list(self) -> list[Order]:
        statement = select(Order).options(selectinload(Order.items)).order_by(Order.id)

        result = await self.session.scalars(statement)

        return list(result.all())

    async def update_total(
        self,
        order: Order,
        total: Decimal,
    ) -> Order:
        order.total = total

        await self.session.flush()

        return order

    async def update_status(
        self,
        order: Order,
        status: OrderStatus,
    ) -> Order:
        order.status = status.value
        await self.session.flush()
        return order
