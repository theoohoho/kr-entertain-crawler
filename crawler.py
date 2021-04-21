import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from enum import Enum


class SourcePlatform(Enum):
    BILIBILI = 'bilibili'
    FRIDAY = 'friday'
    IQIYI = 'iqiyi'
    KKTV = 'kktv'
    YOUTUBE = 'youtu'


class Crawler:
    """Crawler
    """
    _instance = None
    _session = None
    root_url = 'https://www.ptt.cc'
    main_url = root_url + '/bbs/KR_Entertain/index.html'

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    async def fetch_source(self):
        """Fetch target data source
        """
        pass

    def to_html(self):
        """Parsed beautiful soap html data
        """
        pass

    def get_article_title_link(self, soup):
        soup_list = soup.find_all('div', 'r-ent')
        soup_tags = [soup_tag.select_one('a') for soup_tag in soup_list]
        title_links = []
        for soup_tag in soup_tags:
            article_title = soup_tag.text
            if not re.match('.*(\[影音\]).*', article_title):
                continue
            article_url = self.root_url + soup_tag.get('href')
            title_link = (article_title, article_url)
            title_links.append(title_link)
        print(f'Total parsed {len(title_links)} result items!')
        return title_links

    def get_video_url(self, soup):
        source_regex = '|'.join([f'({source_title.value})' for source_title in list(SourcePlatform)])
        parsed_video_html = soup.find_all(
            'a', href=re.compile(f'.*{source_regex}.*'))
        video_links = [i.get('href') for i in parsed_video_html]
        return video_links

    async def get_last_page(self) -> int:
        print('Get last page...')
        async with self._session.get(self.main_url) as resp:
            if resp.status != 200:
                raise Exception(f'Request failed! status code: {resp.status}')
            html_body = await resp.text()
            soup = BeautifulSoup(html_body, "html.parser")
            last_page_url = soup.find('div', class_='btn-group-paging').find_all('a')[1].get('href')
            last_page = re.search('\d+', last_page_url).group()
        return int(last_page) + 1

    async def parse(self, target_page: int):
        print('Parsing target source...')
        target_url = self.root_url + f'/bbs/KR_Entertain/index{target_page}.html'
        async with self._session.get(target_url) as resp:
            if resp.status != 200:
                raise Exception(f'Request failed! status code: {resp.status}')
            html_body = await resp.text()
            soup = BeautifulSoup(html_body, "html.parser")
            return self.get_article_title_link(soup)

    async def parse_article(self, title_link):
        article_title, article_url = title_link
        print(f'Parsing {article_title} for {article_url} ...')
        async with self._session.get(article_url) as resp:
            if resp.status != 200:
                raise Exception(f'Request failed! status code: {resp.status}')
            html_body = await resp.text()
            soup = BeautifulSoup(html_body, "html.parser")
            # make video source regex for extract target link
            video_urls = self.get_video_url(soup)
            print(f'Successfully parsed article: {article_title}')
            return dict(
                article_title=article_title,
                article_url=article_url,
                video_urls=video_urls
            )

    async def parse_articles(self, title_links):
        tasks = [asyncio.create_task(self.parse_article(link)) for link in title_links]
        return await asyncio.gather(*tasks)

    async def crawl(self, page_range: int = 0):
        self._session = aiohttp.ClientSession()
        article_content = []
        # select crawl range that start from last page
        last_page = await asyncio.create_task(self.get_last_page())
        target_pages = [page for page in range(
            last_page, last_page-page_range-1, -1)]
        print(f'Last page is {str(last_page)}')
        print(f'Target page to crawl: {str(target_pages)}')
        for target_page in target_pages:
            title_links = await asyncio.create_task(self.parse(target_page))
            article_content.extend(await self.parse_articles(title_links))
        await self._session.close()

    def extract_data(self):
        """Extract tv show metadata from html data
        """
        pass

    def clean_data(self):
        """Expect to clean html data, and extract tv source link
        """
        pass

    def parse_to_schema(self):
        """Parse data to table schema
        """
        pass

    def store_in_db(self):
        """Store data into database
        """
        pass

    def run(self):
        """Run crawler to do right thing
        """
        asyncio.run(self.crawl())


if __name__ == "__main__":
    c = Crawler()
    c.run()
