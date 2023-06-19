import logging
import asyncio
import re
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from api import *


logging.basicConfig(level=logging.INFO)


bot = Bot(token=os.environ.get('TG_BOT_TOKEN', 'Токен не указан'))
dp = Dispatcher(bot, storage=MemoryStorage())


class BotState(StatesGroup):
    new_project = State()
    project_name = State()
    description = State()
    repository = State()
    config = State()
    start = State()
    restart = State()
    stop = State()
    delete = State()


@dp.message_handler(commands=('start', ), state='*')
async def start(message: types.Message):
    username = message.from_user.username
    await message.answer(f'Здравствуйте, {username}!\n\n'
                        f'🛠 Я - бот по автодеплою веб-проектов на Python и готов помочь '
                        f'Вам с быстрым и лёгким развёртыванием ваших проектов. '
                        f'Благодарим Вас за использование наших услуг!\n\n'
                        f'Для начала развёртывания проекта выполните команду /new')


@dp.message_handler(commands=('new', ), state='*')
async def new_project(message: types.Message):
    await message.answer("Укажите название проекта (=имя поддомена сайта)")
    await BotState.project_name.set()


@dp.message_handler(state=BotState.project_name)
async def process_project_name(message: types.Message, state: FSMContext):
    project_name = message.text.strip()
    pattern = r'^[a-zA-Z0-9-]{1,63}$'
    if not re.match(pattern, project_name):
        await message.answer('Имя проекта невалидно')
        return
    await state.update_data(name=project_name)
    await message.answer("Укажите краткое описание проекта (до 100 символов)")
    await BotState.description.set()


@dp.message_handler(state=BotState.description)
async def process_description(message: types.Message, state: FSMContext):
    description = message.text.strip()
    if len(description) < 5:
        await message.answer('Слишком краткое описание')
        return
    await state.update_data(username=message.from_user.username)
    await state.update_data(id=message.from_user.id)
    await state.update_data(description=description)

    data = await state.get_data()
    response = await create_project(data)
    await message.answer(response)

    await message.answer("Укажите URL git-репозитория в формате `https://github.com/<username>/repository.git`",
                         disable_web_page_preview=True, parse_mode='Markdown')

    await BotState.repository.set()


@dp.message_handler(state=BotState.repository)
async def process_repository_url(message: types.Message, state: FSMContext):
    git_url = message.text.strip()

    pattern = r'https:\/\/(?:[^\s@\/]+@)?github\.com\/.+\/.+(\.git)?'
    print(re.match(pattern, git_url))
    if re.match(pattern, git_url) is None:
        await message.answer("Ошибка в формате ввода URL git-репозитория")
        return
    await state.update_data(repo_url=git_url)
    await message.answer('Выполните команду /config для отправки конфигурационного файла')


@dp.message_handler(commands=('config', ), state='*')
async def config(message: types.Message, state: FSMContext):
    await message.answer("Отправьте конфигурационный файл в формате <b>TXT / JSON</b>\n\n"
                         "❗️Файл должен содержать ПОЛНЫЙ перечень переменных, необходимых для запуска Вашего проекта",
                         parse_mode='html')
    await BotState.config.set()


@dp.message_handler(content_types=('document', ), state=BotState.config)
async def process_config(message: types.Message, state: FSMContext):
    if message.document.mime_type in ('text/plain', 'application/json'):
        file_info = await bot.get_file(message.document.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        file_content = file_bytes.read().decode('utf-8')
        file_name, file_ext = os.path.splitext(file_info.file_path)
        file_ext = file_ext.lstrip('.')
        await state.update_data(config=file_content, ext=file_ext)
        await message.answer('✅ Файл успешно получен')
        await message.answer('Теперь можете запустить проект /run')
        await BotState.start.set()
    else:
        await message.answer('Неверный формат файла! Пожалуйста, отправьте файл с расширением <b>TXT / JSON</b>',
                             parse_mode='html')


@dp.message_handler(commands=('run', ), state='*')
async def run(message: types.Message, state: FSMContext):
    data = await state.get_data()
    response = await start_project(data)
    await message.answer(response)


@dp.message_handler(commands=('restart', ), state='*')
async def restart(message: types.Message, state: FSMContext):
    await BotState.restart.set()
    data = await state.get_data()
    response = await restart_project(data)
    await message.answer(response)


@dp.message_handler(commands=('stop', ), state='*')
async def stop(message: types.Message, state: FSMContext):
    await BotState.stop.set()
    data = await state.get_data()
    response = await stop_project(data)
    await message.answer(response)


@dp.message_handler(commands=('stop', ), state='*')
async def stop(message: types.Message, state: FSMContext):
    await BotState.stop.set()
    data = await state.get_data()
    response = await get_project(message.from_user.id)
    await message.answer(response)


if __name__ == '__main__':
    asyncio.run(dp.start_polling())
