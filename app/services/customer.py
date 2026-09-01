from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate


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
