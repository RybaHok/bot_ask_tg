from asyncio import create_task, sleep

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import ContentType, Message
from fluent.runtime import FluentLocalization


from blocklist import banned, shadowbanned
from config_reader import config
from filters import SupportedMediaFilter

router = Router()


intro = """
добро пожаловать в бот анонимных сообщений 🤗

напишите сюда всё, что хотите мне передать, и через несколько секунд я получу ваше сообщение, но не буду знать от кого.

отправить можно фото, видео, текст, голосовые, видеосообщения (кружки), а также стикеры и гифки.

на данный момент я могу ответить только на голосовые сообщение, фото, видео (не кружки), а также на текстовые сообщения.

но до меня доходят все ваши сообщения 😜 

⚠️ это полностью анонимно!
"""

desc_help = """
Для того чтобы переслать сообщение просто впишите его в 
чат и я автоматически перешлю его хозяйке. 😎😎😎
"""


about = """
https://bio.site/deymyanrina
"""


async def _send_expiring_notification(message: Message, l10n: FluentLocalization):
    """
    Отправляет "самоуничтожающееся" через 3 секунд сообщение

    :param message: сообщение, на которое бот отвечает подтверждением отправки
    :param l10n: объект локализации
    """
    msg = await message.reply(l10n.format_value("Сообщение отправлено!"))
    if config.remove_sent_confirmation:
        await sleep(3.0)
        await msg.delete()


@router.message(Command(commands=["start"]))
async def cmd_start(message: Message, l10n: FluentLocalization):
    """
    Приветственное сообщение от бота пользователю

    :param message: сообщение от пользователя с командой /start
    :param l10n: объект локализации
    """
    await message.answer(l10n.format_value(intro))


@router.message(Command(commands=["help"]))
async def cmd_help(message: Message, l10n: FluentLocalization):
    """
    Справка для пользователя

    :param message: сообщение от пользователя с командой /help
    :param l10n: объект локализации
    """
    await message.answer(l10n.format_value(desc_help))


@router.message(Command(commands=["about"]))
async def cmd_about(message: Message, l10n: FluentLocalization):
    """
    сообщение от бота пользователю контакты

    :param message: сообщение от пользователя с командой /контакты
    :param l10n: объект локализации
    """
    await message.answer(l10n.format_value(about))


@router.message(F.text)
async def text_message(message: Message, bot: Bot, l10n: FluentLocalization):
    """
    Хэндлер на текстовые сообщения от пользователя

    :param message: сообщение от пользователя для админа(-ов)
    :param l10n: объект локализации
    """
    if len(message.text) > 4000:
        return await message.reply(l10n.format_value("Слишком длинный текст максимум 4000 символов"))
    if message.from_user.id in banned:
        await message.answer(l10n.format_value("Вы заблокированы!"))
    elif message.from_user.id in shadowbanned:
        return
    else:
        await bot.send_message(
            config.admin_chat_id,
            message.html_text + f"\n\n#id{message.from_user.id}", parse_mode="HTML",
        )
        create_task(_send_expiring_notification(message, l10n))


@router.message(SupportedMediaFilter())
async def supported_media(message: Message, bot: Bot, l10n: FluentLocalization):
    """
    Хэндлер на медиафайлы от пользователя.
    Поддерживаются только типы, к которым можно добавить подпись (полный список см. в регистраторе внизу)

    :param message: медиафайл от пользователя
    :param l10n: объект локализации
    """
    if message.caption and len(message.caption) > 1000:
        return await message.reply(l10n.format_value("Слишком большой файл"))
    if message.from_user.id in banned:
        await message.answer(l10n.format_value("Вы заблокированы!"))
    elif message.from_user.id in shadowbanned:
        return
    else:
        await message.copy_to(
            config.admin_chat_id,
            caption=((message.caption or "") + f"\n\n\n#id{message.from_user.id}"),
            parse_mode="HTML",
         )
        create_task(_send_expiring_notification(message, l10n))


@router.message()
async def unsupported_types(message: Message, l10n: FluentLocalization):
    """
    Хэндлер на неподдерживаемые типы сообщений, т.е. те, к которым нельзя добавить подпись

    :param message: сообщение от пользователя
    :param l10n: объект локализации
    """
    # Игнорируем служебные сообщения
    if message.content_type not in (
            ContentType.NEW_CHAT_MEMBERS, ContentType.LEFT_CHAT_MEMBER, ContentType.VIDEO_CHAT_STARTED,
            ContentType.VIDEO_CHAT_ENDED, ContentType.VIDEO_CHAT_PARTICIPANTS_INVITED,
            ContentType.MESSAGE_AUTO_DELETE_TIMER_CHANGED, ContentType.NEW_CHAT_PHOTO, ContentType.DELETE_CHAT_PHOTO,
            ContentType.SUCCESSFUL_PAYMENT, "proximity_alert_triggered",  # в 3.0.0b3 нет поддержки этого контент-тайпа
            ContentType.NEW_CHAT_TITLE, ContentType.PINNED_MESSAGE):
        await message.reply(l10n.format_value("Не правильный формат сообщения!"))







