import asyncio
import aiohttp
import aiofiles
import concurrent.futures as C_F
from multiprocessing import cpu_count
from bs4 import BeautifulSoup
from math import floor
from pprint import pprint
import json


async def get_response():
    async with aiohttp.ClientSession() as Client:

        async with Client.get("https://www.ukr.net/") as response:
            if response.status != 200:
                response.raise_for_status()
            page = await response.text()
            soup = BeautifulSoup(page, features="html.parser")
            sections = soup.find_all('section', class_='items')[1:]
            return sections


async def get_items_from_section(section_id, section_list):
    items = section_list[section_id].find_all('div', class_='item')
    news_list = []
    for item in items:
        category = section_list[section_id].find('h2').text
        title = item.find('a').text
        url = item.find('a').get('href')
        source = item.find('span').text[1:-1]
        time = item.find('time').text
        news_list.append(get_object(category, title, url, source, time))
    return news_list


def start_parsing():
    section_list = asyncio.run(get_response())
    for id in range(len(section_list)):
        news_list = asyncio.run(get_items_from_section(id+1, section_list))
        pprint(news_list)

        with open('data.json', 'a', encoding='utf-8') as file:
            json.dump(
                news_list,
                file,
                indent=4,
                ensure_ascii=False)


def get_object(category, title, url, source, time):
    return {'category': category, 'title': title, 'url': url, 'source': source, 'time': time}


def main():
    NUM_PAGES = 100
    NUM_CORES = cpu_count()
    OUTPUT_FILE = './wiki_titles.txt'

    PAGES_PER_CORE = floor(NUM_PAGES/NUM_CORES)
    PAGES_FOR_FINAL = NUM_PAGES - PAGES_PER_CORE * NUM_CORES

    futures = []

    with C_F.ProcessPoolExecutor(NUM_CORES) as executor:
        for i in range(NUM_CORES):
            new_future = executor.submit(
                start_parsing,
                num_pages=PAGES_PER_CORE,
                output_file=OUTPUT_FILE)
            futures.append(new_future)

        futures.append(executor.submit(
            start_parsing,
            num_pages=PAGES_FOR_FINAL,
            output_file=OUTPUT_FILE))

    C_F.wait(futures)


if __name__ == "__main__":
    start_parsing()
