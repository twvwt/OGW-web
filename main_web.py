from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import PyJWTError as JWTError
from passlib.context import CryptContext
import json
import random
import logging
import uuid

from database.models import Product, User, BasketItem, News
from database.engine import session_maker
from sqlalchemy import select, update, delete, insert
from pydantic import BaseModel
from typing import Optional

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="OGWPLUS API", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройки аутентификации
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Модели запросов
class UserCreate(BaseModel):
    user_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None

class UserUpdate(BaseModel):
    address: Optional[str] = None
    delivery_method: Optional[str] = None
    payment_method: Optional[str] = None

class ProductCreate(BaseModel):
    category: str
    postcategory: str
    name: str
    price: float
    new_price: float
    description: str
    image: str

class AddToBasketRequest(BaseModel):
    productId: int
    quantity: int = 1

class CreateOrderRequest(BaseModel):
    address: str
    delivery_method: str
    payment_method: str
    items: list[dict]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

# Middleware для обработки ошибок
@app.middleware("http")
async def catch_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": "Internal server error"}
        )

# Вспомогательные функции
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.user_id == token_data.user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

# API Endpoints
@app.post("/api/users", response_model=User)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверяем, существует ли пользователь
    result = await db.execute(select(User).where(User.user_id == user.user_id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Создаем нового пользователя
    db_user = User(
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@app.get("/api/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.put("/api/users/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    update_data = user_update.dict(exclude_unset=True)
    await db.execute(
        update(User)
        .where(User.user_id == current_user.user_id)
        .values(**update_data)
    )
    await db.commit()
    
    # Получаем обновленного пользователя
    result = await db.execute(select(User).where(User.user_id == current_user.user_id))
    return result.scalars().first()

@app.get("/api/products")
async def get_products(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Product)
    if category:
        query = query.where(Product.category == category)
    
    result = await db.execute(query)
    products = result.scalars().all()
    return [{
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "new_price": p.new_price,
        "description": p.description,
        "image": p.image,
        "category": p.category,
        "postcategory": p.postcategory
    } for p in products]

@app.get("/api/products/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/api/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product.category).distinct())
    categories = result.scalars().all()
    return {"categories": categories}

@app.get("/api/news")
async def get_news(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(News).order_by(News.id.desc()))
    news_items = result.scalars().all()
    return [{
        "id": n.id,
        "text": n.news_text,
        "image": n.photo_id,
        "created_at": n.created
    } for n in news_items]

@app.get("/api/basket", response_model=list[dict])
async def get_basket(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(BasketItem).where(BasketItem.user_id == current_user.user_id))
    basket_items = result.scalars().all()
    return [json.loads(item.product_name) for item in basket_items]

@app.post("/api/basket")
async def add_to_basket(
    item: AddToBasketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Проверяем существование товара
    result = await db.execute(select(Product).where(Product.id == item.productId))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Формируем данные товара для корзины
    product_data = {
        "productId": product.id,
        "name": product.name,
        "price": product.price,
        "image": product.image,
        "quantity": item.quantity,
        "added_at": datetime.now().isoformat()
    }
    
    # Добавляем в корзину
    basket_item = BasketItem(
        user_id=current_user.user_id,
        product_name=json.dumps(product_data)
    )
    db.add(basket_item)
    await db.commit()
    return {"success": True, "product": product_data}

@app.delete("/api/basket/{item_id}")
async def remove_from_basket(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(BasketItem)
        .where(BasketItem.id == item_id)
        .where(BasketItem.user_id == current_user.user_id)
    )
    basket_item = result.scalars().first()
    if not basket_item:
        raise HTTPException(status_code=404, detail="Item not found in basket")
    
    await db.delete(basket_item)
    await db.commit()
    return {"success": True}

@app.post("/api/orders", status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Проверяем, что корзина не пуста
    if not order_data.items:
        raise HTTPException(status_code=400, detail="Basket is empty")
    
    # Создаем заказ
    order_id = str(uuid.uuid4())
    total_amount = sum(item['price'] * item['quantity'] for item in order_data.items)
    
    # Сохраняем заказ в БД
    db_order = Order(
        order_id=order_id,
        user_id=current_user.user_id,
        items=json.dumps(order_data.items),
        total_amount=total_amount,
        address=order_data.address,
        delivery_method=order_data.delivery_method,
        payment_method=order_data.payment_method,
        status="created"
    )
    db.add(db_order)
    
    # Очищаем корзину пользователя
    await db.execute(delete(BasketItem).where(BasketItem.user_id == current_user.user_id))
    
    # Обновляем данные пользователя
    await db.execute(
        update(User)
        .where(User.user_id == current_user.user_id)
        .values(
            address=order_data.address,
            delivery_method=order_data.delivery_method,
            payment_method=order_data.payment_method
        )
    )
    
    await db.commit()
    
    return {
        "success": True,
        "order_id": order_id,
        "total_amount": total_amount,
        "created_at": datetime.now().isoformat()
    }

@app.get("/api/orders")
async def get_user_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.user_id == current_user.user_id).order_by(Order.created.desc()))
    orders = result.scalars().all()
    return [{
        "order_id": o.order_id,
        "total_amount": o.total_amount,
        "status": o.status,
        "created_at": o.created,
        "items": json.loads(o.items)
    } for o in orders]

@app.post("/api/token", response_model=Token)
async def login_for_access_token(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)