from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.sh_products import Product as ProductSchema, ProductCreate
from app.models.m_products import Product as ProductModel
from app.models.m_categories import Category as CategoryModel
from app.DB.db_depends import get_async_db
from app.models.m_users import User as UserModel
from app.auth import get_current_seller

router = APIRouter(prefix='/products', tags=['products'])

@router.get("/", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    stmt = select(ProductModel).where(ProductModel.is_active == True).order_by(ProductModel.id)
    result = await db.scalars(stmt)
    products = result.all()
    return products


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_seller)):
    stmt = select(ProductModel).where(ProductModel.name == product.name, ProductModel.is_active == True)
    result_product = await db.scalars(stmt)
    is_product = result_product.first()
    if is_product != None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product exists")
    
    stmt_2 = select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
    result_category = await db.scalars(stmt_2)
    is_category = result_category.first()
    if is_category != None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category is not found")
    
    product_new = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(product_new)
    await db.commit()
    await db.refresh(product_new)
    return product_new


@router.get("/category/{category_id}", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True) 
    result = await db.scalars(stmt)
    category = result.first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category is not found")
    
    stmt_products = select(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active == True).order_by(ProductModel.id)
    result_products = await db.scalars(stmt_products)
    products = result_products.all()
    return products


@router.get("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def get_products(product_id: int, db: AsyncSession = Depends(get_async_db)):
    stmt_product = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    result = await db.scalars(stmt_product)
    product = result.first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found")
    
    stmt_category = select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
    result_categoty = await db.scalars(stmt_category)
    category = result_categoty.first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category is not found")
    
    return product


@router.put("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def update_products(product_id: int, product: ProductCreate, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_seller)):
    
    stmt_product = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    result_product = await db.scalars(stmt_product)
    product_old = result_product.first()
    if product_old is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found")
    
    if product_old.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")
    
    stmt_category = select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
    result_category = await db.scalars(stmt_category)
    category = result_category.first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category is not found")
    
    await db.execute(update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump()))
    await db.commit()
    await db.refresh(product_old)
    return product_old


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_products(product_id: int, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_seller)):
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    result = await db.scalars(stmt)
    product = result.first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found!")
    
    if product.seller != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own products")
    
    await db.execute(update(ProductModel).where(ProductModel.id == product_id).values(is_active = False))
    await db.commit()
    await db.refresh(product)
    return {
        "status": "success",
        "message": "Product marked is inactive"
    }