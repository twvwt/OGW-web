from aiogram.filters import Filter, BaseFilter
from aiogram import Bot, types
from aiogram.types import Message


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types
        
        
    async def __call__(self, message: types.Message) ->bool:
        return message.chat.type in self.chat_types
    
    
# Собственный фильтр, проверяющий юзера на админа
class IsAdmin(BaseFilter):
    def __init__(self) -> None:
        # В качестве параметра фильтр принимает список с целыми числами 
        self.admin_ids = [703972180, 760307185]
        
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids