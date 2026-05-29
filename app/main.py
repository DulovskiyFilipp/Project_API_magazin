from fastapi import FastAPI
from app.routers import r_categories, r_products

app = FastAPI(title='Мой интеренет магазин', version="0.1.0")

app.include_router(r_categories.router)
app.include_router(r_products.router)

@app.get("/")
async def hello_message() -> dict:
    return {"Message": "Добро пожаловать в мой интернет магазин"}