from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm

from app.models.m_users import User as UserModel
from app.schemas.sh_users import UserCreate, User as UserShema
from app.DB.db_depends import get_async_db
from app.auth import hash_password, verify_password, create_accesse_toker

router = APIRouter(prefix='/users', tags=["users"])

@router.post('/', response_model=UserShema, status_code = status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    user_db = select(UserModel).where(UserModel.email == user.email)
    result = await db.scalars(user_db)
    chek_user = result.first()
    if chek_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
    db_user = UserModel(email = user.email, 
                        hashed_password = hash_password(user.password),
                        role=user.role)
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_db)):
    
    stmt = select(UserModel).where(UserModel.email == form_data.username, UserModel.is_active == True)
    result = await db.scalars(stmt)
    user = result.first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password", 
                            headers={"WWW-Authenticate": "Bearer"})
    
    accesse_token = create_accesse_toker(data={"sub": user.email, "role": user.role, "id": user.id})
    return {"accesse_token": accesse_token,
            "token_type": "bearer"}