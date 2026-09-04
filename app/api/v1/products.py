from fastapi import APIRouter, HTTPException, status

from app.core.database import SessionDep
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product import ProductService

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    data: ProductCreate,
    session: SessionDep,
):
    service = ProductService(session)

    try:
        return await service.create_product(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
async def get_product(
    product_id: int,
    session: SessionDep,
):
    service = ProductService(session)

    product = await service.get_product(product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.get(
    "",
    response_model=list[ProductResponse],
)
async def list_products(
    session: SessionDep,
):
    service = ProductService(session)

    return await service.list_products()


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    session: SessionDep,
):
    service = ProductService(session)

    try:
        product = await service.update_product(
            product_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product
