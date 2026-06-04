from pydantic import BaseModel, Field, ConfigDict, EmailStr

class UserCreate(BaseModel):
    email: EmailStr = Field(description="Email user")
    password: str = Field(min_length=8, description="password (min 8 characters)")
    role: str = Field(default="buyer", pattern="^(buyer|seller)$", description="Role: 'buyer' or 'seller'")
    
class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str
    model_config = ConfigDict(from_attributes=True)