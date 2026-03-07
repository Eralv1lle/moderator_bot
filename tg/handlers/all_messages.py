from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, ChatPermissions
from aiogram.enums import ContentType, ChatMemberStatus

import io
import asyncio
from datetime import datetime, timedelta

from services import moder_agent
from config import config


async def mute(message: Message, bot: Bot):
    until_date = datetime.now() + timedelta(minutes=config.DURATION_MINUTES)
    await bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        permissions=ChatPermissions(can_send_messages=False,
                                    can_send_other_messages=False,
                                    can_pin_messages=False,
                                    can_edit_tag=False,
                                    can_send_polls=False,
                                    can_change_info=False,
                                    can_send_audios=False,
                                    can_send_photos=False,
                                    can_send_videos=False,
                                    can_invite_users=False,
                                    can_manage_topics=False,
                                    can_send_documents=False,
                                    can_send_video_notes=False,
                                    can_send_voice_notes=False,
                                    can_add_web_page_previews=False),
        until_date=until_date
    )


router = Router()


@router.message(F.chat.id == config.GROUP_ID, F.content_type == ContentType.TEXT)
async def handle_message(message: Message, bot: Bot):
    print("ТЕКСТ")
    member = await bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

    if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
        return

    bad = moder_agent.process_text(message.text)

    if bad:
        await bot.send_message(config.ADMIN_ID, f"Пользователь {message.from_user.first_name} @{message.from_user.username}, говорит плохие слова:\n\n{message.text}")
        await message.answer(f"Друг, {message.from_user.first_name} @{message.from_user.username}, так в это группе высказываться нельзя, помолчи {config.DURATION_MINUTES} минут")
        await message.delete()
        await mute(message, bot)


@router.message(F.chat.id == config.GROUP_ID, F.content_type == ContentType.PHOTO)
async def handle_photo(message: Message, bot: Bot):
    print("ФОТО")
    member = await bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

    if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
        return

    photo = message.photo[-1].file_id
    file = io.BytesIO()
    await bot.download(photo, destination=file)

    bad = await asyncio.to_thread(moder_agent.process_image, file)

    if not bad and message.caption:
        bad = await asyncio.to_thread(moder_agent.process_text, message.caption)

    if bad:
        await bot.send_photo(
            chat_id=config.ADMIN_ID,
            photo=photo,
            caption=f"Пользователь {message.from_user.first_name} @{message.from_user.username}, присылает плохие картинки и слова:\n\n{message.caption}"
        )
        await message.answer(f"Друг, {message.from_user.first_name} @{message.from_user.username}, так в это группе высказываться нельзя, помолчи {config.DURATION_MINUTES} минут")
        await message.delete()
        await mute(message, bot)


@router.message(F.chat.id == config.GROUP_ID, F.content_type == ContentType.ANIMATION)
async def handle_gif(message: Message, bot: Bot):
    print("ГИФКА")
    member = await bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

    if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
        return

    gif = message.animation.file_id
    file = io.BytesIO()
    await bot.download(gif, destination=file)

    bad = await asyncio.to_thread(moder_agent.process_gif, file)
    file.seek(0)

    if bad:
        await bot.send_animation(
            chat_id=config.ADMIN_ID,
            animation=gif,
        )
        await bot.send_message(config.ADMIN_ID, f"Пользователь {message.from_user.first_name} @{message.from_user.username}, присылает плохие гифки:\n\n{message.caption}")
        await message.answer(f"Друг, {message.from_user.first_name} @{message.from_user.username}, так в это группе высказываться нельзя, помолчи {config.DURATION_MINUTES} минут")
        await message.delete()
        await mute(message, bot)


@router.message(F.chat.id == config.GROUP_ID, F.sticker)
async def handle_sticker(message: Message, bot: Bot):
    print(f"СТИКЕР")
    member = await bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

    if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
        return

    if message.sticker.is_animated:
        return

    file_io = io.BytesIO()
    await bot.download(message.sticker.file_id, destination=file_io)
    file_io.seek(0)

    if message.sticker.is_video:
        bad = await asyncio.to_thread(moder_agent.process_gif, file_io)
    else:
        bad = await asyncio.to_thread(moder_agent.process_image, file_io)

    if bad:
        await bot.send_sticker(
            chat_id=config.ADMIN_ID,
            sticker=message.sticker.file_id,
        )
        await bot.send_message(config.ADMIN_ID, f"Пользователь {message.from_user.first_name} @{message.from_user.username}, присылает плохие стикеры")
        await message.answer(f"Друг, {message.from_user.first_name} @{message.from_user.username}, так в это группе высказываться нельзя, помолчи {config.DURATION_MINUTES} минут")
        await message.delete()
        await mute(message, bot)


@router.message(F.chat.id == config.GROUP_ID, (F.voice | F.video_note))
async def handle_audio_messages(message: Message, bot: Bot):
    print("ГОЛОСОВОЕ/КРУЖОЧЕК")
    member = await bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

    if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
        return

    file_id = message.voice.file_id if message.voice else message.video_note.file_id

    file_io = io.BytesIO()
    await bot.download(file_id, destination=file_io)
    file_io.seek(0)

    bad = await asyncio.to_thread(moder_agent.process_voice, file_io)

    if bad:
        if message.content_type == ContentType.VOICE:
            await bot.send_voice(
                chat_id=config.ADMIN_ID,
                voice=file_id,
            )
        else:
            await bot.send_video_note(
                chat_id=config.ADMIN_ID,
                video_note=file_id,
            )
        await bot.send_message(config.ADMIN_ID, f"Пользователь {message.from_user.first_name} @{message.from_user.username}, присылает плохие голосовые/кружки")
        await message.answer(f"Друг, {message.from_user.first_name} @{message.from_user.username}, так в это группе высказываться нельзя, помолчи {config.DURATION_MINUTES} минут")
        await message.delete()
        await mute(message, bot)