from aiogram import F, Router

from app.bot.settings import emoji

router_faq = Router()


@router_faq.message(F.text == (emoji["info"] + "FAQ"))
async def handle_faq(message):
    # TODO: REWRITE
    text = """
    """
    await message.answer(text)
