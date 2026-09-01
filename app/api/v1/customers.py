from fastapi import APIRouter, HTTPException, status

from app.core.database import SessionDep
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.services.customer import CustomerService

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer(
    data: CustomerCreate,
    session: SessionDep,
):
    service = CustomerService(session)

    try:
        return await service.create_customer(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
async def get_customer(
    customer_id: int,
    session: SessionDep,
):
    service = CustomerService(session)

    customer = await service.get_customer(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return customer


@router.get(
    "",
    response_model=list[CustomerResponse],
)
async def list_customers(
    session: SessionDep,
):
    service = CustomerService(session)

    return await service.list_customers()
