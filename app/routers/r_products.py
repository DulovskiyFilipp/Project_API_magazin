from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.schemas.sh_products import Product as ProductSchema, ProductCreate
from app.models.m_products import Product as ProductModel
from app.models.m_categories import Category as CategoryModel
from app.DB.db_depends import get_db

router = APIRouter(prefix='/products', tags=['products'])

@router.get("/", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_all_products(db: Session = Depends(get_db)):
    stmt = select(ProductModel).where(ProductModel.is_active == True).order_by(ProductModel.id)
    products = db.execute(stmt).scalars().all()
    return products


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    stmt = select(ProductModel).where(ProductModel.name == product.name, ProductModel.is_active == True)
    is_product = db.execute(stmt).scalars().first()
    if is_product != None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product exists")
    
    product_new = ProductModel(**product.model_dump())
    db.add(product_new)
    db.commit()
    db.refresh(product_new)
    return product_new


@router.get("/category/{category_id}", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True) 
    category = db.execute(stmt).scalars().first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category is not found")
    
    stmt_products = select(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active == True).order_by(ProductModel.id)
    products = db.execute(stmt_products).scalars().all()
    return products


@router.get("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def get_products(product_id: int, db: Session = Depends(get_db)):
    stmt_product = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    product = db.execute(stmt_product).scalars().first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found")
    
    stmt_category = select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
    category = db.execute(stmt_category).scalars().first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category is not found")
    
    return product


@router.put("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def update_products(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    stmt_product = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    product_old = db.execute(stmt_product).scalars().first()
    if product_old is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found")
    
    stmt_category = select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
    category = db.execute(stmt_category).scalars().first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category is not found")
    
    db.execute(update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump()))
    db.commit()
    db.refresh(product_old)
    return product_old


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_products(product_id: int, db: Session = Depends(get_db)):
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    product = db.execute(stmt).scalars().first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found")
    
    db.execute(update(ProductModel).where(ProductModel.id == product_id).values(is_active = False))
    db.commit()
    db.refresh(product)
    return {
        "status": "success",
        "message": "Product marked is inactive"
    }