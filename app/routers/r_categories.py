from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.m_categories import Category as CategoryModel
from app.models.m_products import Product as ProductModel
from app.schemas.sh_categories import Category as CategorySchema, CategoryCreate
from app.DB.db_depends import get_db

router = APIRouter(prefix='/categories', tags=['categories'])

@router.get("/", response_model=list[CategorySchema], status_code=status.HTTP_200_OK)
async def get_all_categories(db: Session = Depends(get_db)):
    stmt = select(CategoryModel).where(CategoryModel.is_active == True).order_by(CategoryModel.id)
    categories = db.execute(stmt).scalars().all()
    return categories


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    if category.parent_id is not None:
        stmt = select(CategoryModel).where(CategoryModel.id == category.parent_id, CategoryModel.is_active == True)
        parent = db.execute(stmt).scalars().first()
        if parent is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent category not found")
        
    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category
    
    
@router.put("/{category_id}", response_model=CategorySchema, status_code=status.HTTP_200_OK)
async def update_category(category_id: int, category: CategoryCreate, db: Session = Depends(get_db)):
    stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True)
    db_category = db.execute(stmt).scalars().first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category.parent_id is not None:
        parent_stmt = select(CategoryModel).where(CategoryModel.id == category.parent_id, CategoryModel.is_active == True)
        parent = db.execute(parent_stmt).scalars().first()
        if parent is None:
            raise HTTPException(status_code=400, detail="Parent category not found")
    
    db.execute(
        update(CategoryModel)
        .where(CategoryModel.id == category_id)
        .values(**category.model_dump())
    )
    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True)
    category = db.execute(stmt).scalars().first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category no found")
    
    db.execute(update(CategoryModel).where(CategoryModel.id == category_id).values(is_active = False))
    db.commit()
    db.refresh(category)
    
    db.execute(update(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active == True).values(is_active = False))
    db.commit()
    
    return{
        "status": "success",
        "message": "Category and product marked is inactive"
    }

