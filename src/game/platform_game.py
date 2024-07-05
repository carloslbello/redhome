from game_platform.game_platform import Platform

class PlatformGame():
    """Class for a game as it exists on a particular game platform."""

    def __init__(self, platform: Platform, id: str):
        self.platform = platform
        self.id = id

    """Get the game's publisher name and install size on disk if it is supportable."""
    async def get_publisher_name_and_install_size_on_disk_for_game_if_supportable(self) -> tuple[str, int] | None:
        data = await self.platform.get_data_for_game_id(self.id)

        if data is None:
            return None

        publisher_name, cloud_support, install_size_on_disk = self.platform.get_publisher_name_cloud_support_and_install_size_on_disk_for_game_data(data)

        if cloud_support:
            return (publisher_name, install_size_on_disk)
        return None

    def __repr__(self):
        return f'<{self.platform.name()}({self.id})>'
