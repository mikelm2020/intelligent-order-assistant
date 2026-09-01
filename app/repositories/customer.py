from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate


class CustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: CustomerCreate) -> Customer:
        customer = Customer(**data.model_dump())

        self.session.add(customer)
        await self.session.flush()
        await self.session.refresh(customer)

        return customer

    async def get_by_id(self, customer_id: int) -> Customer | None:
        return await self.session.get(Customer, customer_id)

    async def get_by_email(self, email: str) -> Customer | None:
        statement = select(Customer).where(Customer.email == email)

        result = await self.session.scalars(statement)

        return result.first()

    async def list(self) -> list[Customer]:
        statement = select(Customer).order_by(Customer.id)

        result = await self.session.scalars(statement)

        return list(result.all())
