import aiohttp

# API address
base_url = 'https://ewdbot.com/api'

# Project emoji statuses
EMOJI_STATUS = {
    'Запущен': '✅',
    'Остановлен': '❌',
}


async def make_request(method, endpoint, data=None):
    """
    Helper function for making HTTP requests.

    :param method: HTTP method (GET, POST, PUT, DELETE)
    :param endpoint: API endpoint
    :param data: Data to send (default None)
    :return: Response as text or error
    """
    async with aiohttp.ClientSession() as session:
        async with session.request(method, f"{base_url}{endpoint}", json=data) as response:
            if response.status in (400, 404):
                return (await response.json()).get('error')
            elif response.status in (200, 201, 204):
                return await response.json()
            # Return an error message for all other cases
            return "Неизвестная ошибка"


async def create_project(data):
    """
    Creating a new project

    :param data: Project data (json)
    :return: Project creation message or error
    """
    response = await make_request('POST', '/projects', data)
    if isinstance(response, dict) and 'message' in response:
        return response['message']
    return response


async def delete_project(data):
    """
    Deleting a project

    :param data: Project data
    :return: Project deletion message or error
    """
    response = await make_request('DELETE', '/projects', data)
    if isinstance(response, dict) and 'message' in response:
        return response['message']
    return response


async def get_project(data):
    """
    Obtaining information about the project.

    :param data: Project data
    :return: Formatted string with project information or error
    """
    response = await make_request('GET', f"/{data}/projects")

    if isinstance(response, dict) and 'projects' in response:
        projects = response['projects']

        # Formatting information about each project
        result_string = '\n\n'.join(
            '\n'.join(
                f"{field}: {value}" for field, value in {
                    'Имя проекта': project['name'],
                    'Описание': project['description'],
                    'Дата создания': project['created_at'],
                    'Статус': EMOJI_STATUS.get(project['status'])
                }.items()
            ) for project in projects
        )

        return result_string
    return response


async def start_project(data):
    """
    Launch of the project

    :param data: Project data
    :return: Project startup message or error
    """
    response = await make_request('PUT', '/projects/start', data)
    if isinstance(response, dict):
        return f"{response.get('message', '')}\n{response.get('link', '')}"
    return response


async def restart_project(data):
    """
    Restarting the project

    :param data: Project data
    :return: Project restart message or error
    """
    response = await make_request('PUT', '/projects/restart', data)
    if isinstance(response, dict):
        return f"{response.get('message', '')}\n{response.get('link', '')}"
    return response


async def stop_project(data):
    """
    Stopping the project

    :param data: Project data
    :return: Project stop message or error
    """
    response = await make_request('PUT', '/projects/stop', data)
    if isinstance(response, dict) and 'message' in response:
        return response['message']
    return response
