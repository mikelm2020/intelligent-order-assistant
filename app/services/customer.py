from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.customer import CustomerHasOrdersError
from app.models.customer import Customer
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = CustomerRepository(session)

    async def create_customer(self, data: CustomerCreate) -> Customer:
        existing_customer = await self.repository.get_by_email(data.email)

        if existing_customer:
            raise ValueError("Customer email already exists")

        customer = await self.repository.create(data)

        await self.session.commit()

        return customer

    async def get_customer(self, customer_id: int) -> Customer | None:
        return await self.repository.get_by_id(customer_id)

    async def list_customers(self) -> list[Customer]:
        return await self.repository.list()

    async def update_customer(
        self,
        customer_id: int,
        data: CustomerUpdate,
    ) -> Customer | None:
        customer = await self.repository.get_by_id(customer_id)

        if customer is None:
            return None

        if data.email is not None and data.email != customer.email:
            existing_customer = await self.repository.get_by_email(data.email)

            if existing_customer:
                raise ValueError("Customer email already exists")

        customer = await self.repository.update(
            customer=customer,
            data=data,
        )

        await self.session.commit()

        return customer

    async def delete_customer(
        self,
        customer_id: int,
    ) -> bool:
        customer = await self.repository.get_by_id(customer_id)

        if customer is None:
            return False

        if await self.repository.has_orders(customer_id):
            raise CustomerHasOrdersError("Customer with orders cannot be deleted")

        await self.repository.delete(customer)
        await self.session.commit()

        return True
