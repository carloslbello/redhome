from itertools import combinations
from game.game import Game
from game.platform_game import PlatformGame
from game_platform.game_platform import Platform

class IGDB():
    def __init__(self, client_session, twitch_client_id: str, twitch_client_secret: str, platforms: list[Platform]):
        self.client_session = client_session
        self.twitch_client_id = twitch_client_id
        self.twitch_client_secret = twitch_client_secret
        self.platforms = platforms

    async def list_games(self):
        games: list[Game] = []

        twitch_access_token: str = (await (await self.client_session.post( f'https://id.twitch.tv/oauth2/token?client_id={self.twitch_client_id}&client_secret={self.twitch_client_secret}&grant_type=client_credentials')).json())['access_token']

        igdb_website_categories_to_platforms: dict[int, Platform] = {}
        possible_igdb_platform_ids_set: set[int] = set()

        for platform in self.platforms:
            igdb_website_categories_to_platforms[platform.igdb_website_category()] = platform
            possible_igdb_platform_ids_set.add(platform.igdb_platform_id())

        possible_igdb_platform_ids_combos = combinations(possible_igdb_platform_ids_set, 2)

        igdb_platform_match_statements = []

        for possible_igdb_platform_combo in possible_igdb_platform_ids_combos:
            igdb_platform_match_statements.append(f'platforms = {str(list(possible_igdb_platform_combo))}')

        offset = 0

        while True:
            resp = await self.client_session.post('https://api.igdb.com/v4/games/', data=f'fields name, websites.category, websites.url; where ({" | ".join(igdb_platform_match_statements)}) & category = 0; limit 500; offset {offset};', headers={'Client-ID': self.twitch_client_id, 'Authorization': f'Bearer {twitch_access_token}'})

            resp_json = await resp.json()

            for game in resp_json:
                if 'websites' not in game:
                    continue
                platform_games = []
                for website in game['websites']:
                    if website['category'] in igdb_website_categories_to_platforms:
                        platform = igdb_website_categories_to_platforms[website['category']]
                        platform_id = platform.get_game_id_from_igdb_website_url(website['url'])
                        if platform_id:
                            platform_games.append(PlatformGame(platform, platform_id))

                if 1 < len(platform_games):
                    games.append(Game(game['name'], platform_games))

            if len(resp_json) != 500:
                break
            offset += 500

        return games
