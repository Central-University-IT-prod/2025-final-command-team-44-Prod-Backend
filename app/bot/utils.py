from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram import Bot as AiogramBot
from aiogram import Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message as AiogramMessage
from aiogram.types import Update
from aiogram.utils.deep_linking import create_start_link, decode_payload
from aiogram_dialog import ChatEvent
from aiogram_dialog.api.internal.manager import DialogManagerFactory
from aiogram_dialog.api.protocols import DialogRegistryProtocol
from aiogram_dialog.context.media_storage import MediaIdStorage
from aiogram_dialog.manager.manager import ManagerImpl
from aiogram_dialog.manager.message_manager import MessageManager
from app.exceptions import ServiceException
from app.services import *


async def create_ref_link(payload):
    from app.bot import bot

    link = await create_start_link(bot, str(payload), encode=True)

    return link


async def extract_payload(message_text: str):
    #from app.bot import bot

    try:
        payload = message_text.removeprefix("/start").strip()

        if not payload:
            raise ServiceException(status_code=400, detail="No payload")

        payload = decode_payload(payload)
        return payload
    except Exception as e:
        pass


class Bot(AiogramBot):
    def __init__(self, token, session=None, **kwargs):
        self.users = UserService()
        self.booking = BookingService()
        self.location = LocationService()
        self.tables = TableService()

        default = DefaultBotProperties(parse_mode=ParseMode.HTML)

        super().__init__(token, session, default, **kwargs)


class Message(AiogramMessage):
    bot: Bot


class DialogManager(ManagerImpl):
    def __init__(
        self, event, message_manager, media_id_storage, registry, router, data
    ):
        from app.bot import bot

        self.bot: Bot = bot

        super().__init__(
            event, message_manager, media_id_storage, registry, router, data
        )


class CustomManager(DialogManagerFactory):
    def __init__(self, **kwargs) -> None:
        self.message_manager = MessageManager()
        self.media_id_storage = MediaIdStorage()

    def __call__(
        self,
        event: ChatEvent,
        data: dict,
        registry: DialogRegistryProtocol,
        router: Router,
    ) -> DialogManager:
        manager = DialogManager(
            event=event,
            data=data,
            message_manager=self.message_manager,
            media_id_storage=self.media_id_storage,
            registry=registry,
            router=router,
        )

        return manager


custom_manager_factory = lambda **kwargs: CustomManager()(**kwargs)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: dict[str:Any],
    ) -> Any:
        user = await message.bot.users.get_or_create(
            message.from_user.id,
            message.from_user.first_name,
            message.from_user.username,
        )

        data["user"] = user

        return await handler(message, data)
