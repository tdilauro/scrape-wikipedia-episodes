#!/usr/bin/env python3

import asyncio
from wikipedia_series import WikipediaSeries

'''
2020-02-08 Tim DiLauro
Scrape episode data from Wikipedia "episode" pages
'''


async def main():

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

    pending = [asyncio.create_task(WikipediaSeries.async_from_url(url)) for url in show_season_urls]
    series = await asyncio.gather(*pending, return_exceptions=True)

    print([s.as_json() for s in series])


if __name__ == "__main__":
    async_event_loop = asyncio.get_event_loop()
    async_event_loop.run_until_complete(main())
    async_event_loop.stop()
