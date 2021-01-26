import json
from math import ceil

import gevent
from gevent import monkey

gevent.monkey.patch_all(thread=False)
import os
import re
import time
import traceback
from abc import ABC
from abc import abstractmethod

from concurrent.futures._base import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from functools import wraps
from urllib.parse import urljoin
from urllib.parse import urlparse

import requests
from selenium import webdriver
from lxml import etree
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from zhconv import convert

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def count_time(func):
    @wraps(func)
    def warpper(*args, **kwargs):
        s_time = time.time()
        res = func(*args, **kwargs)
        e_time = time.time()
        t_time = e_time - s_time
        print('%s耗时：%s' % (func.__name__, t_time))
        return res

    return warpper


class BasePorn(ABC):
    def __init__(self,
                 page_url=None,
                 root_dir='',
                 finish_file_name=None,
                 max_repeat_num=100,
                 wait_time=30,
                 long_wait_time=60,
                 disable_load_img=True,
                 headless=True,
                 proxies={
                     'http': 'http://127.0.0.1:10800',
                     'https': 'https://127.0.0.1:10800',
                 },
                 save_dir=os.path.join(base_dir, 'file'),
                 mutil_thread=True,
                 url_list_xpath='',
                 next_page_xpath='',
                 cookie_file='',
                 max_workers = 5
                 ):
        # 禁止网页加载图片，但是能正常获取图片url，提高爬取速度
        # https://stackoverflow.com/questions/28070315/python-disable-images-in-selenium-google-chromedriver/31581387#31581387

        prefs = {"profile.managed_default_content_settings.images": 2}
        self.options = webdriver.ChromeOptions()
        if headless:
            self.options.add_argument('headless')
        if disable_load_img:
            self.options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=self.options)

        self.wait_time = wait_time
        self.long_wait_time = long_wait_time
        self.repeat_num = 0
        self.max_repeat_num = max_repeat_num
        self.proxies = proxies
        self.convert_type = 'zh-cn'
        self.save_dir = save_dir
        self.finish_file_name = finish_file_name
        self.finish_file = os.path.join(self.save_dir, self.finish_file_name)
        self.root_dir = root_dir
        self.page_url = page_url
        self.mutil_thread = mutil_thread
        self.url_list_xpath = url_list_xpath
        self.next_page_xpath = next_page_xpath
        self.cookie_file = cookie_file
        self.cookie_path = os.path.join(self.save_dir, self.cookie_file)
        self.max_workers = max_workers
        self.get_pre_process()

    def get_pre_process(self):
        res = urlparse(self.page_url)
        self.pre_url = res.scheme + '://' + res.netloc
        try:
            with open(self.finish_file, 'r', encoding='utf8') as f:
                self.content = f.read()
        except FileNotFoundError:
            pass
        # self.set_cookies()

    @abstractmethod
    def get_pic_list(self, detail_url):
        pass

    def check_repeat_url(self, url):
        try:
            parse_url = urlparse(url)
            unique_str = os.path.basename(parse_url.path)
            if unique_str in self.content:
                self.repeat_num += 1
                print('repeat_num:%s' % self.repeat_num)
                print('已经下载过：%s' % (url))
                return True
        except Exception:
            print(traceback.format_exc())

    # @count_time
    def get_url_list(self):
        try:
            self.driver.get(self.page_url)
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(self.driver, self.wait_time)
            wait_xpath = self.url_list_xpath.rsplit('/', maxsplit=1)[0]
            wait.until(EC.presence_of_element_located((By.XPATH, wait_xpath)))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            url_list = selector.xpath(self.url_list_xpath)
        except Exception as e:
            print('get_url_list失败:{}\nException:{}'.format(self.page_url, repr(e)))
            return []
        print('%s:url_list获取完成:%s' % (len(url_list), self.page_url))
        return url_list

    def get_next_page(self, repeat_time=5):
        for i in range(repeat_time):
            try:
                self.driver.get(self.page_url)
                wait = WebDriverWait(self.driver, self.wait_time * (i + 1))
                wait_path = self.next_page_xpath.rsplit('/', maxsplit=1)[0]
                wait.until(EC.presence_of_element_located((By.XPATH, wait_path)))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                next_url = selector.xpath(self.next_page_xpath)[0]
                next_url = urljoin(self.pre_url, next_url)
                print('next_url:%s' % next_url)
                self.page_url = next_url
                return next_url
            except Exception:
                print('获取下一页失败：%s' % self.page_url)
                print(traceback.format_exc())
                if i < repeat_time - 1:
                    time.sleep(self.wait_time * (i + 1))

    def get_pic_name(self, url):
        parse_url = urlparse(url)
        file_name = os.path.basename(parse_url.path)
        suffix = file_name.split('.')[-1]
        if suffix not in ['jpg', 'jpeg', 'png', 'gif']:
            headers = requests.head(url, proxies=self.proxies, timeout=self.long_wait_time).headers
            cd = headers.get('Content-Disposition')
            file_name = cd.split("''")[-1]
        return file_name

    def save_pic(self, url, path):
        name = self.get_pic_name(url)
        pic_path = os.path.join(self.root_dir, path, name)
        if os.path.exists(pic_path):
            print('文件已存在:%s' % pic_path)
            return

        for i in range(5):
            try:
                response = requests.head(url, timeout=10 * 2 ** i)
                status_code = response.status_code
                headers = response.headers
                # headers = requests.head(url, timeout=self.long_wait_time).headers
                if status_code >= 400:
                    print("status_code:%s" % status_code)
                    print("url:%s" % url)
                    return
                pic_size = int(headers.get('content-length', 1024 * 1024))
                pic_weight = ceil(pic_size / 1024 / 1024) * 10 or 10
                content = requests.get(url, timeout=pic_weight * 2 ** i).content
                with open(pic_path, 'wb') as f:
                    f.write(content)
                    print(pic_path)
                    return
            except Exception as e:
                print('保存失败第%d次，url:%s,异常信息:%s' % (i + 1, url, e))
                if i == 4:
                    print(traceback.format_exc())
                    print('save_pic失败：%s' % url)
                time.sleep(i)
                continue

    def record_finish_url(self, finish_url, title):
        try:
            with open(self.finish_file, 'a', encoding='utf8') as f:
                f.write(title + '|' + finish_url + '\n')
        except Exception:
            print('写入失败：%s，标题：%s' % (finish_url, title))
            print(traceback.format_exc())

    def login(self):
        raise NotImplementedError

    def save_cookie(self):
        self.login()
        cookies = self.driver.get_cookies()
        with open(self.cookie_path, 'w', encoding='utf8') as f:
            cookies_json = json.dumps(cookies)
            f.write(cookies_json)

    def set_cookies(self):
        # 设置cookie前需要先打开网页
        self.driver.get(self.page_url)
        with open(self.cookie_path, encoding='utf8') as f:
            cookies_json = f.read()
            cookies = json.loads(cookies_json)
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        # 设置cookie后需要刷新网页，显示登录效果
        self.driver.refresh()

    # @count_time
    def download(self, detail_url):
        success, pic_list, title = self.get_pic_list(detail_url)
        legal_title = re.sub(r"[^\w]", "", title)
        legal_title = convert(legal_title, self.convert_type)
        if not success:
            legal_title = '失败-' + legal_title
        if len(pic_list) < 10:
            print('图片过少:%s' % detail_url)
            return legal_title
        pic_list = [urljoin(self.pre_url, pic_url) for pic_url in pic_list]
        print('开始下载:%s' % detail_url)
        path = os.path.join(self.root_dir, legal_title)

        if not os.path.exists(path):
            os.makedirs(path)
        g_list = []

        for pic_url in pic_list:
            g_list.append(gevent.spawn(self.save_pic, pic_url, legal_title))
        gevent.joinall(g_list)
        return legal_title

    def mutil_thread_download(self, url_list, max_workers=None):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            # https://stackoverflow.com/questions/9336646/python-decorator-with-multiprocessing-fails
            # with ProcessPoolExecutor(max_workers=max_workers) as executor:
            t_dict = {executor.submit(self.download, url): url for url in url_list if
                      not self.check_repeat_url(url)}
            for future in as_completed(t_dict):
                url = t_dict[future]
                try:
                    title = future.result()
                except Exception:
                    print('download异常:%s' % url + '\n', traceback.format_exc())
                else:
                    if title:
                        self.record_finish_url(url, title)

    def single_thread_download(self, url_list):
        for url in url_list:
            if self.check_repeat_url(url):
                continue
            try:
                title = self.download(url)
            except Exception:
                print('download fail:%s' % url)
                print(traceback.format_exc())
            else:
                if title:
                    self.record_finish_url(url, title)

    # @count_time
    def main(self):
        print('开始爬取:{}'.format(self.page_url))
        while True:
            url_list = self.get_url_list()
            url_list = [urljoin(self.pre_url, url) for url in url_list]
            if self.mutil_thread:
                self.mutil_thread_download(url_list, max_workers=self.max_workers)
            else:
                self.single_thread_download(url_list)
            if self.repeat_num > self.max_repeat_num:
                print('重复帖子过多')
                self.driver.quit()
                break
            next_page = self.get_next_page()
            if not next_page:
                print('最后一页:%s' % self.page_url)
                self.driver.quit()
                break
        print('结束爬取:{}'.format(self.page_url))
