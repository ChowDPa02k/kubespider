import logging
import os

import aria2p
import random

from utils.config_reader import AbsConfigReader
from download_provider.provider import DownloadProvider
from api import types
from api.values import Task

ua_list = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.1722.31 Safari/537.36 Edg/112.0.1722.31', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.249 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.192 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.2792.47 Safari/537.36 Edg/129.0.2792.47', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.34 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.2651.31 Safari/537.36 Edg/127.0.2651.31', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.129 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.175 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.1245.78 Safari/537.36 Edg/102.0.1245.78', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.231 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.1370.40 Safari/537.36 Edg/106.0.1370.40', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.166 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.64 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.1938.71 Safari/537.36 Edg/116.0.1938.71', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.5304.93 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.39 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.194 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.1774.93 Safari/537.36 Edg/113.0.1774.93', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.25 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.2277.14 Safari/537.36 Edg/121.0.2277.14', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.2151.9 Safari/537.36 Edg/119.0.2151.9', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.1901.18 Safari/537.36 Edg/115.0.1901.18', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.7 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.2957.7 Safari/537.36 Edg/132.0.2957.7', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.2792.47 Safari/537.36 Edg/129.0.2792.47', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.1343.47 Safari/537.36 Edg/105.0.1343.47', 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.65 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.1264.48 Safari/537.36 Edg/103.0.1264.48', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.2592.14 Safari/537.36 Edg/126.0.2592.14', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.1210.13 Safari/537.36 Edg/101.0.1210.13', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.1938.71 Safari/537.36 Edg/116.0.1938.71', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.95 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.192 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.95 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.3179.23 Safari/537.36 Edg/135.0.3179.23', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.2957.7 Safari/537.36 Edg/132.0.2957.7', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.1587.88 Safari/537.36 Edg/110.0.1587.88', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.64 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.39 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.79 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.1518.14 Safari/537.36 Edg/109.0.1518.14', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.1462.2 Safari/537.36 Edg/108.0.1462.2', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.2849.84 Safari/537.36 Edg/130.0.2849.84', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.3065.30 Safari/537.36 Edg/133.0.3065.30', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.65 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.245 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.1418.78 Safari/537.36 Edg/107.0.1418.78', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.2277.14 Safari/537.36 Edg/121.0.2277.14', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.122 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.2849.84 Safari/537.36 Edg/130.0.2849.84', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.1774.93 Safari/537.36 Edg/113.0.1774.93', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.1264.48 Safari/537.36 Edg/103.0.1264.48', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.119 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.1462.2 Safari/537.36 Edg/108.0.1462.2', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.83 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.2592.14 Safari/537.36 Edg/126.0.2592.14', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.192 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.3065.30 Safari/537.36 Edg/133.0.3065.30', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.1418.78 Safari/537.36 Edg/107.0.1418.78', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.1264.48 Safari/537.36 Edg/103.0.1264.48', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.1462.2 Safari/537.36 Edg/108.0.1462.2', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.52 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.231 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.50 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.61 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.131 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.85 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.1370.40 Safari/537.36 Edg/106.0.1370.40', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.2739.11 Safari/537.36 Edg/128.0.2739.11', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.122 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.3124.98 Safari/537.36 Edg/134.0.3124.98', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.3124.98 Safari/537.36 Edg/134.0.3124.98', 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.39 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.231 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.7 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.1661.3 Safari/537.36 Edg/111.0.1661.3', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.194 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.245 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.2478.46 Safari/537.36 Edg/124.0.2478.46', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.1722.31 Safari/537.36 Edg/112.0.1722.31', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.131 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.1462.2 Safari/537.36 Edg/108.0.1462.2', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.104 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.129 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.2792.47 Safari/537.36 Edg/129.0.2792.47', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.1722.31 Safari/537.36 Edg/112.0.1722.31', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.52 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.2365.51 Safari/537.36 Edg/122.0.2365.51', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.2592.14 Safari/537.36 Edg/126.0.2592.14', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.3065.30 Safari/537.36 Edg/133.0.3065.30', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.231 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.2957.7 Safari/537.36 Edg/132.0.2957.7', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.1823.98 Safari/537.36 Edg/114.0.1823.98', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.2151.9 Safari/537.36 Edg/119.0.2151.9', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.2277.14 Safari/537.36 Edg/121.0.2277.14', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.79 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.211 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.104 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.7 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.104 Safari/537.36']
class Aria2DownloadProvider(DownloadProvider):
    def __init__(self, name: str, config_reader: AbsConfigReader) -> None:
        super().__init__(name, config_reader)
        self.provider_name = name
        self.provider_type = 'aria2_download_provider'
        self.rpc_endpoint_host = ''
        self.rpc_endpoint_port = 0
        self.download_base_path = ''
        self.aria2: aria2p.API = None
        self.secret = ''

    def get_provider_type(self) -> str:
        return self.provider_type

    def provider_enabled(self) -> bool:
        return self.config_reader.read()['enable']

    def provide_priority(self) -> int:
        return self.config_reader.read()['priority']

    def get_defective_task(self) -> list[Task]:
        defective_tasks = []
        downloads = self.aria2.get_downloads()
        for single_download in downloads:
            if single_download.is_waiting:
                # The task queue length is limited, so the status maybe be waiting
                continue
            # in general, we only return the bt pending tasks
            if single_download.progress <= 0.0 and single_download.is_torrent:
                # now remove the tasks
                self.aria2.remove([single_download], force=True)
                pending_task = Task(
                    url='magnet:?xt=urn:btih:' + single_download.info_hash,
                    file_type=types.LINK_TYPE_MAGNET,
                    path=str(single_download.dir).removeprefix(self.download_base_path)
                )
                defective_tasks.append(pending_task)

        return defective_tasks

    def send_torrent_task(self, task: Task) -> TypeError:
        logging.info('Start torrent download:%s', task.url)
        download_path = os.path.join(self.download_base_path, task.path)
        try:
            ret = self.aria2.add_torrent(task.url, options={'dir': download_path})
            logging.info('Create download task result:%s', ret)
            task.task_id = ret.gid
            return None
        except Exception as err:
            logging.warning('Please ensure your aria2 server is ok:%s', err)
            return err
        return None

    def send_magnet_task(self, task: Task) -> TypeError:
        logging.info('Start magnet download:%s', task.url)
        download_path = os.path.join(self.download_base_path, task.path)
        try:
            ret = self.aria2.add_magnet(task.url, options={'dir': download_path})
            logging.info('Create download task result:%s', ret)
            task.task_id = ret.gid
            return None
        except Exception as err:
            logging.warning('Please ensure your aria2 server is ok:%s', err)
            return err

    def send_general_task(self, task: Task) -> TypeError:
        logging.info('Start general file download:%s', task.url)

        if not task.url.startswith('http'):
            return TypeError("Aria2 do not support:" + task.url)

        download_path = os.path.join(self.download_base_path, task.path)
        ua = random.choice(ua_list)
        try:
            opt = {'dir': download_path, 'user-agent': ua}
            file_name = task.extra_param('file_name')
            if file_name:
                opt['out'] = file_name
            ret = self.aria2.add(task.url, options=opt)
            task.task_id = ret[0].gid
            logging.info('Create download task result:%s', ret)
            return None
        except Exception as err:
            logging.warning('Please ensure your aria2-type download server is ok:%s', err)
            return err

    def remove_tasks(self, tasks: list[Task]):
        try:
            downloads = self.aria2.get_downloads()
            self.aria2.remove(downloads, force=True)
        except Exception as err:
            logging.warning('Aria2 remove tasks error:%s', err)

    def load_config(self) -> TypeError:
        cfg = self.config_reader.read()
        self.rpc_endpoint_host = cfg['rpc_endpoint_host']
        self.rpc_endpoint_port = cfg['rpc_endpoint_port']
        self.download_base_path = cfg['download_base_path']
        self.secret = cfg['secret']
        self.aria2 = aria2p.API(
            aria2p.Client(
                host=self.rpc_endpoint_host,
                port=self.rpc_endpoint_port,
                secret=self.secret
            )
        )
