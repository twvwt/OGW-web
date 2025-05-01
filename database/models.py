from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, BigInteger,Float,JSON,Column, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import datetime


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class Product(Base):
    __tablename__ = 'product'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[int] =  mapped_column(String(150), nullable=False)
    postcategory: Mapped[int] = mapped_column(String(150), nullable=False)
    name: Mapped[int] = mapped_column(String(150), nullable=False)
    price: Mapped[int] = mapped_column(Float(asdecimal=False), nullable=False)
    new_price: Mapped[int] = mapped_column(Float(asdecimal=False), nullable=False)
    description : Mapped[str] = mapped_column(Text)
    image: Mapped[str] = mapped_column(String(150))
    
class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)  # Имя
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)    # Фамилия
    # Новые поля для личного кабинета с значениями по умолчанию
    address: Mapped[str] = mapped_column(String(255), nullable=True, default='Не указано')      # Адрес
    delivery_method: Mapped[str] = mapped_column(String(50), nullable=True, default='Не указано')  # Вид доставки
    payment_method: Mapped[str] = mapped_column(String(50), nullable=True, default='Не указано')    # Вид оплаты


class BasketItem(Base):
    __tablename__ = 'basket_item'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    product_name  = mapped_column(JSON, nullable=False) 

class News(Base):
    __tablename__ = 'news'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    photo_id = mapped_column(String, unique=True)
    news_text: Mapped[str] = mapped_column(String, unique=True)
    
    
    