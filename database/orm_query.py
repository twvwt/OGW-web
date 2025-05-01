from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product, BasketItem, User


async def orm_add_product(session: AsyncSession, item: dict):
    obj = Product(
            id=item["_id"],  
            category=item["category"],
            postcategory=item["postcategory"],
            name=item["name"],
            price=float(item["price"]),                
            new_price=float(item["new_price"]),
            description=item["description"],
            image=item["photo"]
            )
    session.add(obj)
    await session.commit()
    
async def orm_add_BasketItem(session: AsyncSession, user_id, product: dict):
        obj = BasketItem(
                user_id = user_id,
                product_name = product
        )
        session.add(obj)
        await session.commit()
        
        
# async def orm_put_category(session: AsyncSession):
#         unique_categories = session.query(Product.category).distinct().all()

#         # Вывод результатов
#         for category in unique_categories:
#                 print(category[0])