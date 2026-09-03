from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.order import (
    CustomerNotFoundError,
    InactiveProductError,
    InsufficientStockError,
    OrderAlreadyCancelledError,
    OrderNotFoundError,
    ProductNotFoundError,
)
from app.models.order import Order
from app.models.order_status import OrderStatus
from app.repositories.customer import CustomerRepository
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.schemas.order import OrderCreate


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.order_repository = OrderRepository(session)
        self.customer_repository = CustomerRepository(session)
        self.product_repository = ProductRepository(session)

    async def create_order(self, data: OrderCreate) -> Order:
        customer = await self.customer_repository.get_by_id(data.customer_id)

        if customer is None:
            raise CustomerNotFoundError("Customer not found")

        order = await self.order_repository.create(
            customer_id=data.customer_id,
        )

        total = Decimal("0.00")

        try:
            for item_data in data.items:
                product = await self.product_repository.get_by_id_for_update(
                    item_data.product_id
                )

                if product is None:
                    raise ProductNotFoundError(
                        f"Product {item_data.product_id} not found"
                    )

                if not product.active:
                    raise InactiveProductError(f"Product {product.id} is inactive")

                if product.stock < item_data.quantity:
                    raise InsufficientStockError(
                        f"Insufficient stock for product {product.id}"
                    )

                unit_price = product.price
                subtotal = unit_price * item_data.quantity

                await self.order_repository.add_item(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=item_data.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )

                await self.product_repository.update_stock(
                    product=product,
                    stock=product.stock - item_data.quantity,
                )

                total += subtotal

            await self.order_repository.update_total(
                order=order,
                total=total,
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        created_order = await self.order_repository.get_by_id(order.id)

        if created_order is None:
            raise RuntimeError("Created order could not be retrieved")

        return created_order

    async def get_order(self, order_id: int) -> Order | None:
        return await self.order_repository.get_by_id(order_id)

    async def list_orders(self) -> list[Order]:
        return await self.order_repository.list()

    async def cancel_order(self, order_id: int) -> Order:
        order = await self.order_repository.get_by_id(order_id)

        if order is None:
            raise OrderNotFoundError("Order not found")

        if order.status == OrderStatus.CANCELLED.value:
            raise OrderAlreadyCancelledError("Order is already cancelled")

        try:
            for item in order.items:
                product = await self.product_repository.get_by_id_for_update(
                    item.product_id
                )

                if product is None:
                    raise RuntimeError(
                        f"Product {item.product_id} could not be retrieved"
                    )

                await self.product_repository.update_stock(
                    product=product,
                    stock=product.stock + item.quantity,
                )

            await self.order_repository.update_status(
                order=order,
                status=OrderStatus.CANCELLED,
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        cancelled_order = await self.order_repository.get_by_id(order.id)

        if cancelled_order is None:
            raise RuntimeError("Cancelled order could not be retrieved")

        return cancelled_order
