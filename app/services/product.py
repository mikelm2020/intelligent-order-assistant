from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProductRepository(session)

    async def create_product(self, data: ProductCreate) -> Product:
        existing_product = await self.repository.get_by_sku(data.sku)

        if existing_product:
            raise ValueError("Product SKU already exists")

        product = await self.repository.create(data)

        await self.session.commit()

        return product

    async def get_product(self, product_id: int) -> Product | None:
        return await self.repository.get_by_id(product_id)

    async def list_products(self) -> list[Product]:
        return await self.repository.list()
