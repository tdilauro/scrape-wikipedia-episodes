import aiohttp
from bs4 import BeautifulSoup
from episode import Episode
import json
import re
import requests


_program_pattern = re.compile(r'\A(?P<program>.*?)\s+\((?P<series_type>.*?)(\s+(?P<series_num>\d+))?\)\Z')
_program_subtitle_pattern = re.compile(r'\A\((?P<series_type>.*?)(\s+(?P<series_num>\d+))?\)\Z')
_quoted_title_pattern = re.compile(r'\A(?P<quote>[\'\"])(?P<value>.*)(?P=quote)\Z')


class WikipediaSeries(object):

    def __init__(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        properties = get_series_properties(soup)
        self.name = properties['title']
        self.subtitle = properties['subtitle']
        self.full_name = properties['full_name']
        self.series_type = properties.get('series_type')
        self.series_num = properties.get('series_num')
        episodes = extract_episodes(soup)
        self.episodes = [Episode(program=self.name, **e) for e in episodes]

    def __repr__(self):
        return '{}("{}" ({} episodes))'.format(self.__class__.__name__, self.full_name, len(self.episodes))

    def as_json_obj(self):
        json_object = {k: v for k, v in self.__dict__.items() if k != 'episodes' }
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
        html = await get_episode_page_html(url)
        return cls(html)


async def get_episode_page_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
        return html


def get_series_properties(soup):
    title_element = soup.select('#firstHeading')[0]
    title = title_element.i.get_text()
    full_name = title_element.get_text()
    subtitle = full_name.replace(title, '', 1).strip()
    properties = parse_program_title(subtitle, pattern=_program_subtitle_pattern)
    properties['title'] = title
    properties['subtitle'] = subtitle
    properties['full_name'] = full_name
    return properties


def parse_program_title(title, pattern=_program_pattern):
    match = re.match(pattern, title)
    if match is not None:
        properties = match.groupdict()
        series_num = properties.get('series_num', None)
        if series_num is not None:
            properties['series_num'] = int(series_num)
    else:
        properties = {'title': title}
    return properties


def extract_episodes(soup):
    episode_tables = soup.find_all('table', 'wikiepisodetable')
    episode_table_count = len(episode_tables)

    table = episode_tables[0]

    heading_cells = table.tbody.tr.find_all('th')
    heading_text = [tag.get_text() for tag in heading_cells]
    column_attrs = heading_attributes(heading_text)

    episode_rows = table.find_all('tr', 'vevent')
    synopses = [tag.get_text() for tag in table.find_all('td', 'description')]
    if len(episode_rows) != len(synopses):
        print("Warning: Number of episode property rows ({}) does not match number of episode description rows ({})"
              .format(len(episode_rows), len(synopses)))

    episodes = []
    for seq, row in enumerate(episode_rows):
        attributes = [row.th.get_text(), *[col.get_text() for col in row.find_all('td')]]
        properties = episode_properties(attributes, column_attrs)
        properties['description'] = synopses[seq]
        episodes.append(properties)

    return episodes

def episode_properties(episode_columns, attributes):
    properties = {}
    for column, value in enumerate(episode_columns):
        value = value.replace(u'\xa0', u' ').replace(u'\u200a', u'')
        attribute = attributes[column]
        if attribute.startswith('number_'):
            try:
                value = int(value)
            except Exception as e:
                pass
        elif attribute == 'title':
            match = re.match(_quoted_title_pattern, value)
            if match is not None:
                value = match.groupdict()['value']

        properties[attribute] = value

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


if __name__ == '__main__':
    s1 = WikipediaSeries.from_url('https://en.wikipedia.org/wiki/Good_Omens_(TV_series)')
    s2 = WikipediaSeries.from_url('https://en.wikipedia.org/wiki/Star_Trek:_Discovery_(season_2)')
    s3 = WikipediaSeries.from_url('https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_1)')
    print(s1, s2, s3, sep="\n")
