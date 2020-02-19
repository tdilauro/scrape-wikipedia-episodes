#!/usr/bin/env python3

import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from urllib.parse import urlsplit

'''
2020-02-08 Tim DiLauro
Scrape episode data from Wikipedia "episode" pages
'''


async def main():

    episodes = []

    def episode_callback(episode):
        episodes.append(episode)

    show_season_urls = [
        'https://en.wikipedia.org/wiki/Star_Trek:_Discovery_(season_1)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_1)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_2)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_3)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_4)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_5)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_6)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_7)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_8)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_9)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_10)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_11)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_12)',
    ]

    pending = [asyncio.create_task(process_url(url, episode_callback)) for url in show_season_urls]
    await asyncio.gather(*pending, return_exceptions=True)

    # episodes.sort(key=lambda e: (strip_season(e[0]), e[1]))
    for episode in sorted(episodes, key=lambda e: (strip_season(e[0]), e[1])):
        print(episode)


async def process_url(url, callback):
    page = await get_episode_page(url)
    episodes = process_page(page, url)
    for episode in episodes:
        callback(episode)


async def get_episode_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            page = await response.text()
        return page


def process_page(page, url):
    soup = BeautifulSoup(page, 'html.parser')

    episode_tables = soup.find_all('table', 'wikiepisodetable')
    episode_table_count = len(episode_tables)
    if episode_table_count != 1:
        print("Unexpected number of episode tables for {}. Found {}, but should be 1.".format(url,
                                                                                              episode_table_count))
        exit(1)

    table = episode_tables[0]
    episode_rows = table.find_all('tr', 'vevent')

    title = urlsplit(url).path.split('/')[-1].replace('_', ' ').strip()
    print("Title: {}".format(title))

    episodes = [episode_properties(title, row) for row in episode_rows]
    return episodes


def episode_properties(title, episode):
    overall_episode_number = int(strip_title(episode.th.get_text()))
    columns = [strip_title(column.get_text()) for column in episode.find_all('td')]
    season_episode_number = int(columns.pop(0))
    return [title, overall_episode_number, season_episode_number, *columns]


def strip_title(title):
    title = title.replace(u'\xa0', u' ').replace(u'\u200a', u'')
    return title.strip().strip("'\"").strip()


def strip_season(title, pattern=re.compile(r'(?i) \(season\s+\d+\)')):
    stripped_title = re.sub(pattern, '', title)
    return stripped_title


if __name__ == "__main__":
    # main()
    async_event_loop = asyncio.get_event_loop()
    async_event_loop.run_until_complete(main())
    async_event_loop.stop()
