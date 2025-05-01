import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.future import select
from database.models import Product, User, BasketItem
import config



# Функция для проверки и создания пользователя
async def get_or_create_user(session: AsyncSession, user_id, first_name, last_name):
    result = await session.execute(select(User).filter_by(user_id=user_id))
    user = result.scalars().first()
    
    if user is None:
        user = User(user_id=user_id, first_name=first_name, last_name=last_name)
        session.add(user)
        await session.commit()
        return user, True
    return user, False

# Функция для поиска пользователя по user_id
async def get_user_by_id(session: AsyncSession, user_id: int) -> User:
    result = await session.execute(select(User).filter_by(user_id=user_id))
    user = result.scalars().first()
    return user

    
async def orm_put_category(session: AsyncSession):
    # Запрос для получения уникальных значений из столбца category
    result = await session.execute(select(Product.category).distinct())
    unique_categories = result.scalars().all()  # Получаем уникальные категории

    # Формируем словарь {'category_{i}': category}
    categories_dict = {f'category_{i}': category for i, category in enumerate(unique_categories)}
    return categories_dict

async def orm_put_postcategory(session: AsyncSession, category_key: str):
    # Получаем все категории
    categories = await orm_put_category(session)
    
    # Извлекаем название категории по индексу
    category_name = categories[f'category_{category_key}']

    # Запрос для получения уникальных значений из столбца postcategory, где category == category_name
    result = await session.execute(
        select(Product.postcategory).where(Product.category == category_name).distinct()
    )
    
    # Получаем все записи, соответствующие условию
    post_categories = sorted(result.scalars().all())  # Получаем все значения

    # Формируем словарь {'postcategory_{i}': post_category}
    postcategories_dict = {f'postcategory_{i}': post_category for i, post_category in enumerate(post_categories)}
    
    return category_name, postcategories_dict

async def orm_put_products_by_postcategory(session: AsyncSession, category_key, postcategory_key):
    # Получаем все подкатегории
    category_name, postcategories = await orm_put_postcategory(session, category_key)
    
    # Извлекаем название подкатегории по индексу
    postcategory_name = postcategories[f'postcategory_{postcategory_key}']

    # Запрос для получения всех продуктов, соответствующих подкатегории
    result_name = await session.execute(
        select(Product).where(Product.postcategory == postcategory_name)
    )
    
    # Получаем все продукты, соответствующие условию
    products = result_name.scalars().all()

    # Формируем словарь {'product_{i}': {'name': new_price}}
    products_dict = {f'product_{i}': {'name': product.name, 'price': product.price, 'description': product.description, 'photo':product.image} for i, product in enumerate(products)}
    return postcategory_name, products_dict



