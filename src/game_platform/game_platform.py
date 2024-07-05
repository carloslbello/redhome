from abc import ABC, abstractmethod

class Platform(ABC):
    """Abstract base class for a game platform whose games' cloud save support and file size can be queried."""

    """Returns the name of the game platform."""
    @staticmethod
    @abstractmethod
    def name() -> str:
        return 'Default platform'

    """Returns the primary IGDB platform ID that this game platform supports."""
    @staticmethod
    @abstractmethod
    def igdb_platform_id() -> int:
        return -1

    """Returns the IGDB website category for this game platform."""
    @staticmethod
    @abstractmethod
    def igdb_website_category() -> int:
        return -1

    """Returns a game's ID if it can be found from IGDB's matching website URL."""
    @staticmethod
    @abstractmethod
    def get_game_id_from_igdb_website_url(igdb_website_url: str) -> str | None:
        return None

    """Returns data from the platform for a specific game for use with `get_cloud_support_for_game_data` and `get_install_size_on_disk_for_game_data`."""
    @abstractmethod
    async def get_data_for_game_id(self, id: str) -> bytes | None:
        return None

    """Using platform data, returns the game publisher's name, whether the game supports cloud save, and its expected installed size on disk."""
    @staticmethod
    @abstractmethod
    def get_publisher_name_cloud_support_and_install_size_on_disk_for_game_data(data: bytes) -> tuple[str, bool, int]:
        return ('', False, 0)

    def __repr__(self):
        return f'<{self.name()}>'
