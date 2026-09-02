from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())

        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)

        return product

    async def get_by_id(self, product_id: int) -> Product | None:
        return await self.session.get(Product, product_id)

    async def get_by_sku(self, sku: str) -> Product | None:
        statement = select(Product).where(Product.sku == sku)

        result = await self.session.scalars(statement)

        return result.first()

    async def list(self) -> list[Product]:
        statement = select(Product).order_by(Product.id)

        result = await self.session.scalars(statement)

        return list(result.all())

    async def update_stock(
        self,
        product: Product,
        stock: int,
    ) -> Product:
        product.stock = stock

        await self.session.flush()

        return product

    async def get_by_id_for_update(
        self,
        product_id: int,
    ) -> Product | None:
        statement = select(Product).where(Product.id == product_id).with_for_update()

        result = await self.session.scalars(statement)

        return result.first()
