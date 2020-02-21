import aiohttp
from bs4 import BeautifulSoup
from episode import Episode
import functools
import json
import operator
import re
import requests

'''
2020-02-08 Tim DiLauro
Scrape episode data from Wikipedia "episode" pages
'''

_series_name_pattern = re.compile(r'\A(?P<name>.*?)\s+\((?P<series_type>.*?)(\s+(?P<series_num>\d+))?\)\Z')
_series_subtitle_pattern = re.compile(r'\A\((?P<series_type>.*?)(\s+(?P<series_num>\d+))?\)\Z')
_quoted_value_pattern = re.compile(r'\A(?P<quote>[\'\"])(?P<value>.*)(?P=quote)\Z')


class WikipediaSeries(object):

    def __init__(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        properties = _get_series_properties(soup)
        self.name = properties['name']
        self.subtitle = properties['subtitle']
        self.full_name = properties['full_name']
        self.series_type = properties.get('series_type')
        self.series_num = properties.get('series_num')
        episodes = _extract_episodes(soup)
        self.episodes = [Episode(program=self.name, **e) for e in episodes]

    def __repr__(self):
        return '{}("{}" ({} episodes))'.format(self.__class__.__name__, self.full_name, len(self.episodes))

    def as_json_obj(self):
        json_object = {k: v for k, v in self.__dict__.items() if k != 'episodes'}
        json_object['episodes'] = [e.__dict__ for e in self.episodes]
        return json_object

    def as_json(self):
        return json.dumps(self.as_json_obj())

    @classmethod
    def from_url(cls, url):
        html = requests.get(url).content
        return cls(html)

    @classmethod
    async def async_from_url(cls, url):
        html = await _async_fetch_url_content(url)
        return cls(html)


async def _async_fetch_url_content(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
        return content


def _get_series_properties(soup):
    heading_element = soup.select('#firstHeading')[0]
    name = heading_element.i.get_text()
    full_name = heading_element.get_text()
    subtitle = full_name.replace(name, '', 1).strip()
    properties = _parse_series_name(subtitle, pattern=_series_subtitle_pattern)
    properties['name'] = name
    properties['subtitle'] = subtitle
    properties['full_name'] = full_name
    return properties


def _parse_series_name(name, pattern=_series_name_pattern):
    match = re.match(pattern, name)
    if match is not None:
        properties = match.groupdict()
        series_num = properties.get('series_num', None)
        if series_num is not None:
            properties['series_num'] = int(series_num)
    else:
        properties = {'name': name}
    return properties


def _extract_episodes(soup):
    episode_tables = soup.find_all('table', 'wikiepisodetable')
    episodes_by_table = [_episodes_from_table(table) for table in episode_tables]
    episodes = _flatten(episodes_by_table)
    return episodes


def _flatten(list_of_lists):
    return functools.reduce(operator.iconcat, list_of_lists, [])


def _episodes_from_table(table):
    heading_cells = table.tbody.tr.find_all('th')
    heading_text = [tag.get_text() for tag in heading_cells]
    column_attrs = _compute_heading_attributes(heading_text)
    episode_rows = table.select('tr.vevent')
    episodes = []
    for seq, row in enumerate(episode_rows):
        attributes = [row.th.get_text(), *[col.get_text() for col in row.find_all('td')]]
        properties = _compute_episode_properties(attributes, column_attrs)
        # assume description, if present, is in row following fielded episode attributes
        description_elements = row.next_sibling.select('td.description')
        if description_elements:
            properties['description'] = description_elements[0].get_text()
        episodes.append(properties)
    return episodes


def _compute_episode_properties(episode_columns, attributes):
    properties = {}
    for column, value in enumerate(episode_columns):
        value = value.replace(u'\xa0', u' ').replace(u'\u200a', u'')
        attribute = attributes[column]
        if attribute.startswith('number_'):
            try:
                value = int(value)
            except ValueError:
                pass
        elif attribute == 'title':
            value = _remove_matching_outer_quotes(value)

        properties[attribute] = value

    return properties


def _remove_matching_outer_quotes(value, value_pattern=_quoted_value_pattern):
    match = re.match(value_pattern, value)
    if match is not None:
        value = match.groupdict()['value']
    return value


def _compute_heading_attributes(headings):
    properties = []
    for i, heading in enumerate(headings):
        text = heading.lower()
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


if __name__ == '__main__':
    s1 = WikipediaSeries.from_url('https://en.wikipedia.org/wiki/Good_Omens_(TV_series)')
    s2 = WikipediaSeries.from_url('https://en.wikipedia.org/wiki/Star_Trek:_Discovery_(season_2)')
    s3 = WikipediaSeries.from_url('https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_1)')
    print(s1, s2, s3, sep="\n")
