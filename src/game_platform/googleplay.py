from asyncio import create_subprocess_shell, Lock, subprocess
import logging
from urllib.parse import urlparse, parse_qs
from game_platform.game_platform import Platform

logger = logging.getLogger(__name__)

class GooglePlay(Platform):
    """Google Play platform class."""

    def __init__(self, raccoon_path: str):
        self.raccoon_path = raccoon_path
        self.raccoon_lock = Lock()

    @staticmethod
    def name() -> str:
        return 'Google Play'

    @staticmethod
    def igdb_platform_id() -> int:
        return 34

    @staticmethod
    def igdb_website_category() -> int:
        return 12

    @staticmethod
    def get_game_id_from_igdb_website_url(igdb_website_url: str) -> str | None:
        parsed_url = urlparse(igdb_website_url)
        netloc_matches = False
        if parsed_url.netloc == 'market.android.com':
            logger.warning('Found a market.android.com URL from IGDB. Consider updating the relevant game''s website on IGDB to a play.google.com URL')
            logger.warning(f'URL: {igdb_website_url}')
            netloc_matches = True
        if parsed_url.netloc == 'play.google.com':
            netloc_matches = True
        if netloc_matches:
            parsed_query = parse_qs(parsed_url.query)
            if 'id' in parsed_query:
                return parsed_query['id'][0]
        return None

    async def get_data_for_game_id(self, id: str) -> bytes | None:
        async with self.raccoon_lock:
            logger.info(f'Getting data for {id}...')
            for tries in range(3):
                stdout, stderr = await (await create_subprocess_shell(f'java -jar {self.raccoon_path} --gpa-details {id}', None, subprocess.PIPE, subprocess.PIPE)).communicate()
                if len(stdout) != 0:
                    return stdout
                if stderr == b'Connection error: Item not found.\n':
                    return None
                logger.warning(f'Raccoon issue attempting to get info for {id}:')
                if stderr:
                    logger.warning(f'Raccoon error: {stderr.decode().strip()}')
                else:
                    logger.warning(f'Raccoon gave no output.')
                logger.warning(f'{2 - tries} tries remaining')
            return None

    @staticmethod
    def get_publisher_name_cloud_support_and_install_size_on_disk_for_game_data(data: bytes) -> tuple[str, bool, int]:
        creator_line_idx = data.find(b'\n  creator: "')
        creator = data[creator_line_idx + 13:data.find(b'"', creator_line_idx + 13)].decode()
        total_apk_size_line_idx = data.find(b'\n        totalApkSize: ')
        if total_apk_size_line_idx == -1:
            size = 0
        else:
            size = int(data[total_apk_size_line_idx + 23:data.find(b'\n', total_apk_size_line_idx + 23)])
        return (creator, data.find(b'\n        1: "Saved Games"') != -1, size)
