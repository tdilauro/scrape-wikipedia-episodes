import aiohttp
from bs4 import BeautifulSoup
from episode import Episode
import json
import re
import requests


_program_pattern = re.compile(r'\A(?P<program>.*?)\s+\((?P<group_type>.*?)(\s+(?P<group_num>\d+))?\)\Z')
_program_subtitle_pattern = re.compile(r'\A\((?P<group_type>.*?)(\s+(?P<group_num>\d+))?\)\Z')
_title_pattern = re.compile(r'\A(?P<quote>[\'\"])(?P<value>.*)(?P=quote)\Z')


class WikipediaSeries(object):

    def __init__(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        properties = get_series_properties(soup)
        self.program = properties['title']
        self.subtitle = properties['subtitle']
        self.full_title = properties['full_title']
        self.group_type = properties.get('group_type')
        self.group_num = properties.get('group_num')
        episodes = extract_episodes(soup)
        self.episodes = [Episode(program=self.program, **e) for e in episodes]

    def __repr__(self):
        return '{}("{}")'.format(self.__class__.__name__, self.full_title)

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
    full_title = title_element.get_text()
    subtitle = full_title.replace(title, '', 1).strip()
    properties = parse_program_title(subtitle, pattern=_program_subtitle_pattern)
    properties['title'] = title
    properties['subtitle'] = subtitle
    properties['full_title'] = full_title
    return properties


def parse_program_title(title, pattern=_program_pattern):
    match = re.match(pattern, title)
    if match is not None:
        properties = match.groupdict()
        group_num = properties.get('group_num', None)
        if group_num is not None:
            properties['group_num'] = int(group_num)
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
    synopsis_rows = [tag.get_text() for tag in table.find_all('td', 'description')]
    if len(episode_rows) != len(synopsis_rows):
        print("Warning: Number of episode property rows ({}) does not match number of episode description rows ({})"
              .format(len(episode_rows), len(synopsis_rows)))

    episodes = [[e.th.get_text(), *[col.get_text() for col in e.find_all('td')]] for e in episode_rows]
    episodes = [episode_properties(episode, column_attrs) for episode in episodes]
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
            match = re.match(_title_pattern, value)
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
    import requests
    p1 = requests.get('https://en.wikipedia.org/wiki/Good_Omens_(TV_series)').content
    p2 = requests.get('https://en.wikipedia.org/wiki/Star_Trek:_Discovery_(season_1)').content
    p3 = requests.get('https://en.wikipedia.org/wiki/The_Big_Bang_Theory_(season_1)').content
    s1 = WikipediaSeries(p1)
    s2 = WikipediaSeries(p2)
    s3 = WikipediaSeries(p3)
