import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import require_owner
from backend.app.db.session import get_db
from backend.app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from backend.app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(db: AsyncSession = Depends(get_db)):
    """Публичный список активных продуктов (без авторизации)."""
    return await product_service.list_products(db, active_only=True)


@router.get("/all", response_model=list[ProductResponse], dependencies=[Depends(require_owner)])
async def list_all_products(db: AsyncSession = Depends(get_db)):
    """Все продукты включая неактивные — только product_owner / super_admin."""
    return await product_service.list_products(db, active_only=False)


@router.post("", response_model=ProductResponse, status_code=201, dependencies=[Depends(require_owner)])
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    return await product_service.create_product(db, data)


@router.patch("/{product_id}", response_model=ProductResponse, dependencies=[Depends(require_owner)])
async def update_product(product_id: uuid.UUID, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    return await product_service.update_product(db, product_id, data)
