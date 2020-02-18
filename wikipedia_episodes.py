from bs4 import BeautifulSoup
import requests
from urllib.parse import urlsplit

'''
2020-02-08 Tim DiLauro
Scrape episode names
'''


def main():
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

    for url in show_season_urls:
        title = urlsplit(url).path.split('/')[-1].replace('_', ' ').strip()
        print("\nTitle: {}".format(title))
        handle_season(url)


def handle_season(wp_url):
    page = requests.get(wp_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    episode_tables = soup.find_all('table', 'wikiepisodetable')
    episode_table_count = len(episode_tables)
    if episode_table_count != 1:
        print("Unexpected number of episode tables for {}. Found {}, but should be 1.".format(wp_url,
                                                                                              episode_table_count))
        exit(1)

    table = episode_tables[0]
    episodes = table.find_all('tr', 'vevent')

    for episode in episodes:
        number_overall = strip_title(episode.th.get_text())
        columns = [strip_title(column.get_text()) for column in episode.find_all('td')]
        print(number_overall, columns)


def strip_title(title):
    title = title.replace(u'\xa0', u' ').replace(u'\u200a', u'')
    return title.strip().strip("'\"").strip()


if __name__ == "__main__":
    main()
