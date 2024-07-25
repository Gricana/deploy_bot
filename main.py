import logging
import asyncio
import re
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from api import *


# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("bot.log"),
                              logging.StreamHandler()])

# Загрузка сэмпла диалога
with open('messages.json', 'r') as f:
    messages = json.load(f)

# Создание экземпляра бота
bot = Bot(token=os.environ.get('TG_BOT_TOKEN', 'Токен не указан'))
storage = Redis(host='localhost', port=6379, db=5)
dp = Dispatcher(bot, storage=storage)


# Определение состояний бота
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


# Обработчик команды /start
@dp.message_handler(commands=('start', ), state='*')
async def start(message: types.Message):
    username = message.from_user.username
    await message.answer(messages["start"].format(username=username))


# Обработчик команды /new
@dp.message_handler(commands=('new', ), state='*')
async def new_project(message: types.Message):
    await message.answer(messages["new_project"])
    await BotState.project_name.set()


# Обработчик ввода названия проекта
@dp.message_handler(state=BotState.project_name)
async def process_project_name(message: types.Message, state: FSMContext):
    project_name = message.text.strip()
    pattern = r'^[a-zA-Z0-9-]{1,63}$'
    if not re.match(pattern, project_name):
        await message.answer(messages["invalid_project_name"])
        return
    await state.update_data(name=project_name)
    await message.answer(messages["description"])
    await BotState.description.set()


# Обработчик ввода описания проекта
@dp.message_handler(state=BotState.description)
async def process_description(message: types.Message, state: FSMContext):
    description = message.text.strip()
    if len(description) < 5:
        await message.answer(messages["short_description"])
        return
    await state.update_data(username=message.from_user.username)
    await state.update_data(id=message.from_user.id)
    await state.update_data(description=description)

    data = await state.get_data()
    response = await create_project(data)
    await message.answer(response)

    await message.answer(messages["repository"],
                         disable_web_page_preview=True,
                         parse_mode='Markdown')

    await BotState.repository.set()


# Обработчик ввода URL git-репозитория
@dp.message_handler(state=BotState.repository)
async def process_repository_url(message: types.Message, state: FSMContext):
    git_url = message.text.strip()

    pattern = r'https:\/\/(?:[^\s@\/]+@)?github\.com\/.+\/.+(\.git)?'
    if re.match(pattern, git_url) is None:
        await message.answer(messages["invalid_git_url"])
        return
    await state.update_data(repo_url=git_url)
    await message.answer(messages["config"])


# Обработчик команды /config
@dp.message_handler(commands=('config', ), state='*')
async def config(message: types.Message, state: FSMContext):
    await message.answer(messages["config_prompt"], parse_mode='html')
    await BotState.config.set()


# Обработчик загрузки конфигурационного файла
@dp.message_handler(content_types=('document', ), state=BotState.config)
async def process_config(message: types.Message, state: FSMContext):
    if message.document.mime_type in ('text/plain', 'application/json'):
        file_info = await bot.get_file(message.document.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        file_content = file_bytes.read().decode('utf-8')
        file_name, file_ext = os.path.splitext(file_info.file_path)
        file_ext = file_ext.lstrip('.')
        await state.update_data(config=file_content, ext=file_ext)
        await message.answer(messages["file_received"])
        await message.answer(messages["run_prompt"])
        await BotState.start.set()
    else:
        await message.answer(messages["invalid_file_format"], parse_mode='html')


# Обработчик команды /run
@dp.message_handler(commands=('run', ), state='*')
async def run(message: types.Message, state: FSMContext):
    data = await state.get_data()
    response = await start_project(data)
    await message.answer(response)


# Обработчик команды /restart
@dp.message_handler(commands=('restart', ), state='*')
async def restart(message: types.Message, state: FSMContext):
    await BotState.restart.set()
    data = await state.get_data()
    response = await restart_project(data)
    await message.answer(response)


# Обработчик команды /stop
@dp.message_handler(commands=('stop', ), state='*')
async def stop(message: types.Message, state: FSMContext):
    await BotState.stop.set()
    data = await state.get_data()
    response = await stop_project(data)
    await message.answer(response)

# Запуск бота
if __name__ == '__main__':
    asyncio.run(dp.start_polling())
