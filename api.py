import aiohttp


base_url = 'https://ewdbot.com/api'


async def create_project(data):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{base_url}/projects', json=data) as response:
            if response.status == 400:
                return response.json()['error']
            elif response.status == 201:
                return response.json()['message']


async def delete_project(data):
    async with aiohttp.ClientSession() as session:
        async with session.delete(f'{base_url}/projects', json=data) as response:
            if response.status == 400:
                return response.json()['error']
            elif response.status == 204:
                return response.json()['message']


async def get_project(data):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/{data}/projects") as response:
            if response.status == 404:
                return response.json()['error']
            elif response.status == 200:
                projects = await response.json()['projects']
                formatted_projects = []
                for project in projects:
                    formatted_project = {
                        'Имя проекта': project['name'],
                        'Описание': project['description'],
                        'Дата создания': project['created_at'],
                        'Статус': get_status_emoji(project['status'])
                    }
                    formatted_projects.append(formatted_project)

                project_strings = []
                for project in formatted_projects:
                    project_string = '\n'.join([f"{field}: {value}" for field, value in project.items()])
                    project_strings.append(project_string)

                result_string = '\n\n'.join(project_strings)
                return result_string


async def start_project(data):
    async with aiohttp.ClientSession() as session:
        async with session.put(f'{base_url}/projects/start', json=data) as response:
            if response.status == 400:
                return response.json()['error']
            elif response.status == 200:
                response = await response.json()
                return f"{response['message']}\n{response['link']}"


async def restart_project(data):
    async with aiohttp.ClientSession() as session:
        async with session.put(f'{base_url}/projects/restart', json=data) as response:
            if response.status == 400:
                return response.json()['error']
            elif response.status == 200:
                response = await response.json()
                return f"{response['message']}\n{response['link']}"


async def stop_project(data):
    async with aiohttp.ClientSession() as session:
        async with session.put(f'{base_url}/projects/stop', json=data) as response:
            if response.status == 400:
                return response.json()['error']
            elif response.status == 200:
                return response.json()['message']


def get_status_emoji(status):
    if status == 'Запущен':
        return '✅'
    elif status == 'Остановлен':
        return '❌'
    else:
        return status
