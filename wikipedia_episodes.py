#!/usr/bin/env python3

import argparse
import asyncio
from wikipedia_series import WikipediaSeries

'''
2020-02-08 Tim DiLauro
Scrape episode data from Wikipedia "episode" pages
'''

def main(urls):
    series = [WikipediaSeries.from_url(url) for url in urls]
    return series


async def async_main(urls):
    pending = [asyncio.create_task(WikipediaSeries.async_from_url(url)) for url in urls]
    series = await asyncio.gather(*pending, return_exceptions=True)
    return series


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sync', action='store_true', help='Use synchronous, rather than asynchronous, retrieval')
    parser.add_argument('urls', nargs='+')
    args = parser.parse_args()

    urls = args.urls

    if args.sync:
        series = main(args.urls)
    else:
        async_event_loop = asyncio.get_event_loop()
        series = async_event_loop.run_until_complete(async_main(args.urls))
        async_event_loop.stop()

    for s in series:
        print(s.as_json())
