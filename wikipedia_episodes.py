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
        'https://en.wikipedia.org/wiki/Good_Omens_(TV_series)',
        'https://en.wikipedia.org/wiki/Star_Trek:_Discovery_(season_1)',
        'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_1)',
        # 'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_2)',
        # 'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_3)',
        # 'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_4)',
        # 'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_5)',
        # 'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_6)',
        # 'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_7)',
        # 'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_8)',
        # 'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_9)',
        # 'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_10)',
        # 'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_11)',
        # 'https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_12)',
    ]

    pending = [asyncio.create_task(process_url(url, episode_callback)) for url in show_season_urls]
    await asyncio.gather(*pending, return_exceptions=True)

    # episodes.sort(key=lambda e: (strip_season(e[0]), e[1]))
    for episode in sorted(episodes, key=lambda e: (e['program'], e['number_in_program'])):
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
    title = urlsplit(url).path.split('/')[-1].replace('_', ' ').strip()
    print("Title: {}".format(title))

    soup = BeautifulSoup(page, 'html.parser')

    episode_tables = soup.find_all('table', 'wikiepisodetable')
    episode_table_count = len(episode_tables)
    if episode_table_count != 1:
        print("Unexpected number of episode tables for {}. Found {}, but should be 1.".format(url,
                                                                                              episode_table_count))
        exit(1)

    table = episode_tables[0]

    heading_cells = table.tbody.tr.find_all('th')
    heading_text = [tag.get_text() for tag in heading_cells]
    column_attrs = heading_attributes(heading_text)


    episode_rows = table.find_all('tr', 'vevent')
    synopsis_rows = [tag.get_text() for tag in table.find_all('td', 'description')]
    if len(episode_rows) == len(synopsis_rows):
       pass
    else:
        print("Warning: Number of episode property rows ({}) does not match number of episode description rows ({})"
              "at url '{}'".format(len(episode_rows), len(synopsis_rows), url))

    episodes = [[e.th.get_text(), *[col.get_text() for col in e.find_all('td')]] for e in episode_rows]
    episodes = [episode_properties(title, episode, column_attrs) for episode in episodes]
    return episodes

program_pattern = re.compile(r'\A(?P<program>.*?)\s+\((?P<group_type>.*?)(\s+(?P<group_num>\d+))?\)\Z')
title_pattern = re.compile(r'\A(?P<quote>[\'\"])(?P<value>.*)(?P=quote)\Z')

def episode_properties(program_title, episode_columns, attributes):
    properties = parse_program_title(program_title)
    for column, value in enumerate(episode_columns):
        attribute = attributes[column]
        if attribute.startswith('number_'):
            try:
                value = int(value)
            except Exception as e:
                pass
        elif attribute == 'title':
            match = re.match(title_pattern, value)
            if match is not None:
                value = match.groupdict()['value']

        properties[attribute] = value

    return properties

def parse_program_title(title, pattern=program_pattern):
    match = re.match(pattern, title)
    if match is not None:
        properties = match.groupdict()
        group_num = properties.get('group_num', None)
        if group_num is not None:
            properties['group_num'] = int(group_num)
    else:
        properties = {'program': title}
    return properties

def heading_attributes(headings):
    properties = []
    for i, heading in enumerate(headings):
        text = heading.lower()
        attribute = None
        if text.startswith('no.'):
            attribute = 'number_in_program'
        elif 'title' in text:
            attribute = 'title'
        elif 'directed' in text or 'director' in text:
            attribute = 'directors'
        elif 'writer' in text or 'written' in text:
            attribute = 'writers'
        elif 'release' in text:
            attribute = 'release'
        elif 'air' in text or 'broadcast' in text:
            attribute = 'air'
        else:
            attribute = heading

        properties.append(attribute)

    if properties[1] == 'number_in_program':
        properties[1] = 'number_in_series'

    return properties


def strip_title(title):
    title = title.replace(u'\xa0', u' ').replace(u'\u200a', u'')
    return title.strip().strip("'\"").strip()


def strip_season(title, pattern=re.compile(r'(?i) \(season\s+\d+\)\s+$')):
    stripped_title = re.sub(pattern, '', title)
    return stripped_title


if __name__ == "__main__":
    async_event_loop = asyncio.get_event_loop()
    async_event_loop.run_until_complete(main())
    async_event_loop.stop()
