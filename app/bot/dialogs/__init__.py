from aiogram import Dispatcher
from aiogram_dialog import setup_dialogs as setup
from app.bot.utils import custom_manager_factory

dialogs = []


def setup_dialogs(dp: Dispatcher):
    for dialog in dialogs:
        dp.include_router(dialog)
    setup(dp, dialog_manager_factory=custom_manager_factory)
