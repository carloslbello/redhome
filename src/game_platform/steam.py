from asyncio import Lock, sleep
import json
import logging
from game_platform.game_platform import Platform

logger = logging.getLogger(__name__)

class Steam(Platform):
    """Steam platform class."""

    def __init__(self, client_session):
        self.client_session = client_session
        self.session_lock = Lock()

    @staticmethod
    def name() -> str:
        return 'Steam'

    @staticmethod
    def igdb_platform_id() -> int:
        return 6

    @staticmethod
    def igdb_website_category() -> int:
        return 13

    @staticmethod
    def get_game_id_from_igdb_website_url(igdb_website_url: str) -> str | None:
        for item in igdb_website_url.split('/'):
            if item.isdigit():
                return item
        return None

    async def get_data_for_game_id(self, id: str) -> bytes | None:
        async with self.session_lock:
            await sleep(3)
            logger.info(f'Getting data for {id}...')
            wait_factor = 1
            while True:
                resp = await self.client_session.get(f'https://store.steampowered.com/api/appdetails?appids={id}')
                if resp.status == 429:
                    wait_minutes = 2 ** wait_factor
                    logger.warning(f'Ratelimited by Steam Store API - waiting {wait_minutes}m before trying again')
                    await sleep(wait_minutes * 60)
                    wait_factor += 1
                    continue
                return await resp.read()

    @staticmethod
    def get_publisher_name_cloud_support_and_install_size_on_disk_for_game_data(data: bytes) -> tuple[str, bool, int]:
        game_dictionary = next(iter(json.loads(data).values()))
        if 'data' not in game_dictionary:
            return ('', False, 0)
        game_dictionary = game_dictionary['data']

        category_ids = list(map(lambda category_obj: category_obj['id'], game_dictionary['categories']))

        cloud_support = 23 in category_ids and 35 not in category_ids

        publisher_list = game_dictionary['publishers']

        if 1 < len(publisher_list):
            logger.warning(f'Multiple publishers found in data for {game_dictionary["name"]} ({game_dictionary["steam_appid"]}): {", ".join(publisher_list)}')
            logger.warning('Only returning the first one')

        pc_requirements = game_dictionary['pc_requirements']
        if not isinstance(pc_requirements, dict):
            return (publisher_list[0], cloud_support, 0)
        storage_string = game_dictionary['pc_requirements']['minimum']
        storage_start_idx = storage_string.find('<strong>Storage:</strong> ')
        if storage_start_idx != -1:
            storage_start_idx += 26
        else:
            storage_start_idx = storage_string.find('<strong>Hard Drive:</strong> ')
            if storage_start_idx != -1:
                storage_start_idx += 29
            else:
                storage_start_idx = storage_string.find('<strong>Hard Disk Space:</strong> ')
                if storage_start_idx != -1:
                    storage_start_idx += 34
                else:
                    return (publisher_list[0], cloud_support, 0)

        storage_string = storage_string[storage_start_idx:].strip().replace(' ', '').replace('+', '').lower()
        storage_string = storage_string[:storage_string.find('b') + 1].replace('mb', '000000').replace('gb', '000000000')
        if '.' in storage_string:
            zeroes_to_remove = storage_string.find('0') - storage_string.find('.') - 1
            storage_string = storage_string.replace('.', '')[:-zeroes_to_remove]
        return (publisher_list[0], cloud_support, int(storage_string))
