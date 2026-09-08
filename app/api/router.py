from fastapi import APIRouter

from app.api.v1.assistant import router as assistant_router
from app.api.v1.customers import router as customers_router
from app.api.v1.documents import router as documents_router
from app.api.v1.orders import router as orders_router
from app.api.v1.products import router as products_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(customers_router)
api_router.include_router(products_router)
api_router.include_router(orders_router)
api_router.include_router(documents_router)
api_router.include_router(assistant_router)
