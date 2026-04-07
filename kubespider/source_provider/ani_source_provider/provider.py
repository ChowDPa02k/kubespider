# This works for: https://open.ani.rip
# Function: download anime updated on ANi project
# encoding:utf-8
import logging
import traceback
import xml.etree.ElementTree as ET
import re
from dataclasses import dataclass
from typing import Optional

from source_provider import provider
from api import types
from api.values import Event, Resource
from utils import helper
from utils.config_reader import AbsConfigReader


DEFAULT_SEASON_MAPPER = {
    "第二季": 2,
    "第三季": 3,
    "第四季": 4,
    "第五季": 5,
    "第六季": 6,
    "第七季": 7,
    "第八季": 8,
    "第九季": 9,
    "第十季": 10,
}
ANIME_TITLE_PATTERN = re.compile(
    r'\[ANi\] (.+?) - (\d+(?:\.5)?) \[(.+?)\]\[(.+?)\]\[(.+?)\]\[(.+?)\]\[(.+?)\]\.'
)
SEASON_RENAME_PATTERN = re.compile(r"- (\d+) \[(720P|1080P|4K)\]\[(Baha|Bilibili)\]")


@dataclass
class AnimeReleaseInfo:
    title: str
    episode: str

    @property
    def is_special_episode(self) -> bool:
        return self.episode.endswith('.5')


class AniSourceProvider(provider.SourceProvider):
    '''This provider is to sync resources from ANi API: https://api.ani.rip/ani-download.xml
    For the most timely follow-up of Anime updates.
    Downloading media in general HTTP, aria2 provider must be needed.
    '''
    def __init__(self, name: str, config_reader: AbsConfigReader) -> None:
        super().__init__(config_reader)
        self.provider_listen_type = types.SOURCE_PROVIDER_PERIOD_TYPE
        self.webhook_enable = False
        self.provider_type = 'ani_source_provider'
        self.api_type = ''
        self.rss_link = ''
        self.rss_link_torrent = ''
        self.tmp_file_path = '/tmp/'
        self.save_path = 'ANi'
        self.provider_name = name
        self.use_sub_category = False
        self.classification_on_directory = True
        self.blacklist = []
        self.custom_season_mapping = {}
        self.custom_category_mapping = {}
        self.season_episode_adjustment = {}

    def _get_custom_season_mapping_rule(self, keyword: str) -> tuple[int, str]:
        mapping = self.custom_season_mapping.get(keyword)
        if isinstance(mapping, dict):
            season = mapping.get('season')
            reserve_keywords = mapping.get('reserve_keywords', '')
            if season is None:
                logging.warning('Invalid custom_season_mapping for %s: missing season field', keyword)
                return 1, reserve_keywords
            return season, reserve_keywords
        return mapping, ''

    def get_provider_name(self) -> str:
        return self.provider_name

    def get_provider_type(self) -> str:
        return self.provider_type

    def get_provider_listen_type(self) -> str:
        return self.provider_listen_type

    def get_download_provider_type(self) -> str:
        return None

    def get_season(self, title: str) -> tuple[int, Optional[str], str]:
        season = 1
        keyword = None
        reserve_keywords = ''
        for kw, value in DEFAULT_SEASON_MAPPER.items():
            if kw in title:
                season = value
                keyword = kw
        for kw in self.custom_season_mapping:
            if kw in title:
                season, reserve_keywords = self._get_custom_season_mapping_rule(kw)
                keyword = kw
        return season, keyword, reserve_keywords

    def replace_keyword(self, title: str, keyword: Optional[str], reserve_keywords: str = '') -> str:
        if not keyword:
            return title
        replacement = f" {reserve_keywords}" if reserve_keywords else ""
        return title.replace(f" {keyword}", replacement)

    def get_adjusted_episode(self, title: str, season: int, episode: str) -> str:
        adjusted_episode = int(episode)
        for target_title, season_mapping in self.season_episode_adjustment.items():
            if target_title in title and season in season_mapping:
                adjusted_episode += season_mapping[season]
        return str(adjusted_episode).zfill(2)

    def rename_season(
        self,
        title: str,
        season: int,
        keyword: Optional[str],
        episode: str,
        reserve_keywords: str = ''
    ) -> str:
        season_ = str(season).zfill(2)
        normalized_title = self.replace_keyword(title, keyword, reserve_keywords)
        adjusted_episode = self.get_adjusted_episode(title, season, episode)
        return SEASON_RENAME_PATTERN.sub(
            rf"- S{season_}E{adjusted_episode} [\2][\3]",
            normalized_title
        )

    def get_subcategory(self, title: str, season: int, keyword: Optional[str]) -> str:
        # Custom subcategory mapping will cover any generated data
        for mapped_keyword, category in self.custom_category_mapping.items():
            if mapped_keyword in title:
                return category
        # Avoid '/' appear in original Anime title
        # This will be misleading for qbittorrent
        sub_category = title.replace('/', '_')
        if ' - ' in title:
            # Drop English Title
            sub_category = sub_category.split(' - ')[-1]
        if season > 1 and keyword:
            # Add Season subcategory
            season_ = str(season).zfill(2)
            sub_category = sub_category.replace(f" {keyword}", '') + f"/Season {season_}"
        # According to qbittorrent issue 19941
        # The Windows/linux illegal symbol of path will be automatically replaced with ' '
        # But if the last char of category string is illegal symbol
        # The replaced ' ' end of a path will occur unexpected bug in explorer
        if sub_category[-1] in "<>:\"/\\|?* ":
            sub_category = sub_category[:-1] + "_"
        # Idk why there's one more space ' ' between English Name and Chinese Name
        # The regex just looks fine
        if sub_category[0] == ' ':
            sub_category = sub_category[1:]
        return sub_category

    def should_skip_release(self, xml_title: str, blacklist: list[str], release_info: Optional[AnimeReleaseInfo]) -> bool:
        if release_info is None:
            return True
        if self.check_blacklist(xml_title, blacklist):
            return True
        if release_info.is_special_episode:
            logging.info('Skip special episode by default: %s', xml_title)
            return True
        return False

    def normalize_resource_url(self, url: str) -> str:
        if 'resources.ani.rip' not in url:
            return url
        return url.replace('resources.ani.rip', 'cloud.ani-download.workers.dev')

    def build_resource(
        self,
        xml_title: str,
        anime_info: AnimeReleaseInfo,
        season: int,
        season_keyword: Optional[str],
        reserve_keywords: str,
        final_url: str,
    ) -> Resource:
        resource = Resource(
            url=final_url,
            path=self.save_path + (f'/{anime_info.title}' if self.classification_on_directory else ''),
            file_type=types.FILE_TYPE_VIDEO_TV,
            link_type=self.get_link_type(),
        )

        if self.api_type == 'torrent' and self.use_sub_category:
            sub_category = self.get_subcategory(anime_info.title, season, season_keyword)
            logging.info('Using subcategory: %s', sub_category)
            resource.put_extra_params({'sub_category': sub_category})

        file_name = xml_title
        if season > 1:
            file_name = self.rename_season(
                xml_title,
                season,
                season_keyword,
                anime_info.episode,
                reserve_keywords,
            )
        resource.put_extra_params({'file_name': file_name})
        return resource

    def parse_resource_item(self, item: ET.Element, blacklist: list[str]) -> Optional[Resource]:
        xml_title = item.findtext('./title')
        anime_info = self.get_anime_info(xml_title)
        if self.should_skip_release(xml_title, blacklist, anime_info):
            return None

        season, season_keyword, reserve_keywords = self.get_season(xml_title)
        logging.info('Found Anime "%s" Season %s Episode %s', anime_info.title, season, anime_info.episode)
        final_url = self.normalize_resource_url(item.findtext('./guid'))
        return self.build_resource(
            xml_title,
            anime_info,
            season,
            season_keyword,
            reserve_keywords,
            final_url,
        )

    def get_prefer_download_provider(self) -> list:
        downloader_names = self.config_reader.read().get('downloader', None)
        if downloader_names is None:
            return None
        if isinstance(downloader_names, list):
            return downloader_names
        return [downloader_names]

    def get_download_param(self) -> dict:
        return self.config_reader.read().get('download_param', {})

    def get_link_type(self) -> str:
        return types.LINK_TYPE_TORRENT if self.api_type == 'torrent' else types.LINK_TYPE_GENERAL

    def provider_enabled(self) -> bool:
        return self.config_reader.read().get('enable', True)

    def is_webhook_enable(self) -> bool:
        return self.webhook_enable

    def should_handle(self, event: Event) -> bool:
        return False

    def get_links(self, event: Event) -> list[Resource]:
        try:
            req = helper.get_request_controller()
            api = self.rss_link_torrent if self.api_type == 'torrent' else self.rss_link
            links_data = req.get(api, timeout=30).content
        except Exception as err:
            logging.info('Error while fetching ANi API: %s', err)
            return []
        tmp_xml = helper.get_tmp_file_name('') + '.xml'
        with open(tmp_xml, 'wb') as cfg_file:
            cfg_file.write(links_data)
            cfg_file.close()
        blacklist = self.load_filter_config()
        return self.get_links_from_xml(tmp_xml, blacklist)

    def get_links_from_xml(self, tmp_xml, blacklist) -> list[Resource]:
        try:
            resources = []
            for item in ET.parse(tmp_xml).findall('.//item'):
                resource = self.parse_resource_item(item, blacklist)
                if resource is not None:
                    resources.append(resource)
            return resources
        except Exception as err:
            print(traceback.format_exc())
            logging.info('Error while parsing RSS XML: %s', err)
            return []

    def get_anime_info(self, title: str) -> Optional[AnimeReleaseInfo]:
        '''Extract info by only REGEX, might be wrong in extreme cases.
        '''
        matches = ANIME_TITLE_PATTERN.match(title)
        if matches is None:
            logging.warning('Error while running regex on title %s', title)
            return None
        anime_title = matches.group(1)
        episode = matches.group(2)
        return AnimeReleaseInfo(title=anime_title, episode=episode)

    def load_filter_config(self) -> str:
        filter_ = self.config_reader.read().get('blacklist', None)

        if filter_ is None or filter_ == "":
            return []
        if isinstance(filter_, list):
            return [str(item) for item in filter_]
        if isinstance(filter_, str):
            return [filter_]
        logging.warning('Invalid blacklist value: %s, fallback to Empty', filter_)
        return []

    def check_blacklist(self, text: str, blacklist: list) -> bool:
        for item in blacklist:
            if item in text:
                logging.info('File %s will be ignored due to blacklist matched: %s', text, item)
                return True
        return False

    def update_config(self, event: Event) -> None:
        pass

    def load_config(self) -> None:
        cfg = self.config_reader.read()
        logging.info('Ani will use %s API', cfg.get('api_type'))
        self.api_type = cfg.get('api_type')
        self.rss_link = cfg.get('rss_link')
        self.rss_link_torrent = cfg.get('rss_link_torrent')
        self.use_sub_category = cfg.get('use_sub_category', False)
        self.classification_on_directory = cfg.get('classification_on_directory', True)
        self.custom_season_mapping = cfg.get('custom_season_mapping', {})
        self.custom_category_mapping = cfg.get('custom_category_mapping', {})
        self.season_episode_adjustment = cfg.get('season_episode_adjustment', {})
