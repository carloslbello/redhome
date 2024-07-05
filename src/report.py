import asyncio
from csv import DictWriter
from itertools import combinations
import logging
from os import environ
from aiohttp import ClientSession
from dotenv import load_dotenv
from pylcs import lcs_string_length
from game_platform.googleplay import GooglePlay
from game_platform.steam import Steam
from igdb import IGDB

logging.basicConfig(level=logging.INFO)

def sameness_heuristic(a: str, b: str) -> bool:
    a_without_spaces = a.replace(' ', '')
    b_without_spaces = b.replace(' ', '')
    return min(len(a_without_spaces), len(b_without_spaces)) * 4/5 < lcs_string_length(a_without_spaces.lower(), b_without_spaces.lower())


async def generate_report(report_path: str):
    load_dotenv()

    fieldnames = ['Game']
    rows = []

    async with ClientSession() as client_session:
        platforms = [Steam(client_session), GooglePlay(environ['RACCOON_PATH'])]
        igdb = IGDB(client_session, environ['TWITCH_CLIENT_ID'], environ['TWITCH_CLIENT_SECRET'], platforms)

        for platform in platforms:
            fieldnames.extend([f'{platform.name()} publisher', f'{platform.name()} install size', f'{platform.name()} ID'])

        for platform_pair in combinations(platforms, 2):
            fieldnames.append(f'{platform_pair[0].name()} / {platform_pair[1].name()} publisher match')

        games = await igdb.list_games()

        game_names = []
        game_dict_from_platforms_to_publisher_name_install_size_and_id_tasks = []

        for game in games:
            game_names.append(game.name)
            game_dict_from_platforms_to_publisher_name_install_size_and_id_tasks.append(game.get_dictionary_from_platform_to_publisher_name_install_size_and_id())

        for idx, dict_from_platform_to_publisher_name_install_size_and_id in enumerate(await asyncio.gather(*game_dict_from_platforms_to_publisher_name_install_size_and_id_tasks)):
            if 1 < sum(value is not None for value in dict_from_platform_to_publisher_name_install_size_and_id.values()):
                row = {'Game': game_names[idx]}
                for platform in dict_from_platform_to_publisher_name_install_size_and_id:
                    if dict_from_platform_to_publisher_name_install_size_and_id[platform] is not None:
                        row[f'{platform.name()} publisher'], row[f'{platform.name()} install size'], row[f'{platform.name()} ID'] = dict_from_platform_to_publisher_name_install_size_and_id[platform]
                for platform_pair in combinations(filter(lambda platform: platform in dict_from_platform_to_publisher_name_install_size_and_id.keys(), platforms), 2):
                    row[f'{platform_pair[0].name()} / {platform_pair[1].name()} publisher match'] = sameness_heuristic(dict_from_platform_to_publisher_name_install_size_and_id[platform_pair[0]][0], dict_from_platform_to_publisher_name_install_size_and_id[platform_pair[1]][0])
                rows.append(row)

    with open(report_path, 'w') as report_file:
        writer = DictWriter(report_file, fieldnames)
        writer.writeheader()
        writer.writerows(rows)

games = asyncio.run(generate_report('report.csv'))
