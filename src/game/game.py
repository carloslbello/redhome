import asyncio
from game.platform_game import PlatformGame
from game_platform.game_platform import Platform

class Game():
    """Class for a game as it exists on multiple game platforms."""

    def __init__(self, name: str, platform_games: list[PlatformGame]):
        self.name = name
        self.platform_games = platform_games

    """Returns a dictionary from platform object to tuple of publisher name, install size in bytes, and ID if cloud save is supported, or None if it is not."""
    async def get_dictionary_from_platform_to_publisher_name_install_size_and_id(self) -> dict[Platform, tuple[str, int, str] | None]:
        result = {}
        platforms = []
        game_ids = []
        get_publisher_name_and_install_size_tasks = []
        for platform_game in self.platform_games:
            platforms.append(platform_game.platform)
            game_ids.append(platform_game.id)
            get_publisher_name_and_install_size_tasks.append(platform_game.get_publisher_name_and_install_size_on_disk_for_game_if_supportable())

        for idx, publisher_name_and_install_size in enumerate(await asyncio.gather(*get_publisher_name_and_install_size_tasks)):
            if publisher_name_and_install_size is not None:
                publisher_name, install_size = publisher_name_and_install_size
                result[platforms[idx]] = (publisher_name, install_size, game_ids[idx])

        return result

    def __repr__(self):
        representation = f'<"{self.name}"'
        if len(self.platform_games) != 0:
            representation += ' ' + (' '.join(map(repr, self.platform_games)))
        representation += '>'
        return representation
