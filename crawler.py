import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from enum import Enum
from model import TV_EPISODE, TV_SHOW, TV_CHANNEL
from database import get_db_session


class SourcePlatform(Enum):
    BILIBILI = 'bilibili'
    FRIDAY = 'friday'
    IQIYI = 'iqiyi'
    KKTV = 'kktv'
    YOUTUBE = 'youtu'


# The element index in TV SHOW Tittle
class TitleInfoIndex:
    publish = 1
    channel = 2
    title = 3
    episode = 4


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
        self.crawler_result = []

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
        # select crawl range that start from last page
        last_page = await asyncio.create_task(self.get_last_page())
        target_pages = [page for page in range(last_page, last_page-page_range-1, -1)]
        print(f'Last page is {str(last_page)}')
        print(f'Target page to crawl: {str(target_pages)}')
        for target_page in target_pages:
            title_links = await asyncio.create_task(self.parse(target_page))
            self.crawler_result.extend(await self.parse_articles(title_links))
        await self._session.close()

    def extract_data(self):
        """Extract tv show metadata from html data
        """
        pass

    def get_tv_metadata(self, db_session) -> tuple:
        tv_channels = db_session.query(TV_CHANNEL).all()
        tv_shows = db_session.query(TV_SHOW.id, TV_SHOW.title).select_from(TV_SHOW).all()
        return (tv_channels, tv_shows)

    def clean_data(self, db_session, tv_channels: list) -> list:
        """Expect to clean html data, and extract tv source link
        """
        print('To clean crawled data....')
        channel_ht = {}
        cleaned_result, channel_regex = [], []

        for channel in tv_channels:
            channel_ht[channel.name] = channel.id
            channel_regex.append(channel.name)

        channel_regex = f'({"|".join(channel_regex)})'

        for result in self.crawler_result:
            title_info = result.get('article_title')
            tv_channel = re.search(channel_regex, title_info)
            if not tv_channel:
                print(f"Data can\'t parsed, the title is: {title_info}")
                continue

            # replace title info that match with tv channel name to blank
            title_info = re.sub(channel_regex, '', title_info.upper())
            tv_channel = tv_channel.group()
            # select specific index
            title_info = title_info.split(' ')
            video_source_link = ','.join(result.get('video_urls'))

            cleaned_result.append(dict(
                tv_show_title=title_info[TitleInfoIndex.title],
                episode_name=title_info[TitleInfoIndex.episode],
                source_link=video_source_link,
                publish_date=title_info[TitleInfoIndex.publish],
                description='',
                tv_channel=tv_channel,
                tv_channel_id=channel_ht.get(tv_channel)
            ))

        return cleaned_result

    def parse_to_schema(self, db_session, shows, complete_result: list) -> None:
        """Parse data to table schema
        """
        print('To parsed cleaned data into table model....')
        existed_tvshow_ht = {}

        for show in shows:
            existed_tvshow_ht[show.title] = show.id

        for tvshow_info in complete_result:
            tvshow_title = tvshow_info.get('tv_show_title')
            tv_show_id = existed_tvshow_ht.get(tvshow_title)

            if tv_show_id is None:
                created_tvshow = TV_SHOW(
                    title=tvshow_title,
                    description=tvshow_info.get('description'),
                    tv_channel_id=tvshow_info.get('tv_channel_id')
                )
                db_session.add(created_tvshow)
                db_session.flush()
                db_session.refresh(created_tvshow)
                tv_show_id = created_tvshow.id

            created_tv_episode = TV_EPISODE(
                name=tvshow_info.get('episode_name'),
                publish_date=tvshow_info.get('publish_date'),
                tv_show_id=tv_show_id,
                source_link=tvshow_info.get('video_source_link')
            )
            db_session.add(created_tv_episode)

    def store_in_db(self) -> None:
        """Store data into database
        """
        with get_db_session() as db_session:
            channels, shows = self.get_tv_metadata(db_session)
            complete_result = self.clean_data(db_session, channels)
            self.parse_to_schema(db_session, shows, complete_result)
            db_session.commit()
            print('Successfully store data into database....')

    def run(self):
        """Run crawler to do right thing
        """
        asyncio.run(self.crawl())
        self.store_in_db()


if __name__ == "__main__":
    c = Crawler()
    c.run()
