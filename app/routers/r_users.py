import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm

from app.models.m_users import User as UserModel
from app.schemas.sh_users import UserCreate, User as UserShema, RefreshTokenRequest
from app.DB.db_depends import get_async_db
from app.auth import hash_password, verify_password, create_accesse_toker, create_refresh_token
from app.config import SECRET_KEY, ALGORITM


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


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_db)):
    
    try: 
        stmt = select(UserModel).where(UserModel.email == form_data.username, UserModel.is_active == True)
        result = await db.scalars(stmt)
        user = result.first()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Incorrect email or password", 
                                headers={"WWW-Authenticate": "Bearer"})
        
        accesse_token = create_accesse_toker(data={"sub": user.email, "role": user.role, "id": user.id})
        refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role, "id": user.id})
        return {"accesse_token": accesse_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"}
    except Exception as e:
        return e
    
@router.post("/refresh_token")
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate refresh token", headers={"WWW-Authenticate": "Bearer"})
    
    old_refresh_token = body.refresh_token
    
    try: 
        payload = jwt.decode(old_refresh_token, SECRET_KEY, algorithms=ALGORITM)
        email: str | None = payload.get("sub")
        token_type: str | None = payload.get("token_type")
        
        if email is None or token_type != "refresh":
            raise credentials_exception
        
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.PyJWKError:
        raise credentials_exception
    
    stmt = select(UserModel).where(UserModel.email == email, UserModel.is_active == True)
    result = await db.scalars(stmt)
    user = result.first()
    if user is None:
        raise credentials_exception
    
    new_refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role, "id": user.id})
    
    return {"refresh_token": new_refresh_token, "token_type": "bearer"}