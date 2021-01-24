import gevent
from gevent import monkey

gevent.monkey.patch_all(thread=False)
import os
import re
import time
import traceback
from concurrent.futures._base import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from functools import wraps
from math import ceil
from urllib.parse import urljoin, urlsplit, parse_qs
from urllib.parse import urlparse

import requests
from lxml import etree

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from zhconv import convert

from config import nineporn_password, nineporn_username


def count_time(fun):
    @wraps(fun)
    def warpper(*args, **kwargs):
        s_time = time.time()
        res = fun(*args, **kwargs)
        e_time = time.time()
        t_time = e_time - s_time
        print('%s耗时：%s' % (fun.__name__, t_time))
        return res

    return warpper


class NinePorn():
    options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    type_dict = {
        'gem': {
            'page_url': 'https://f1113.wonderfulday30.live/forumdisplay.php?fid=19&filter=digest',
            'root_dir': r'E:\爬虫\91精华'
        },
        'ori_gem': {
            'page_url': 'https://f1113.wonderfulday30.live/forumdisplay.php?fid=4&filter=digest',
            'root_dir': r'E:\爬虫\91原创精华'
        },
        'ori': {
            'page_url': 'https://f1113.wonderfulday30.live/forumdisplay.php?fid=4',
            'root_dir': r'E:\爬虫\91原创'
        },
        'all': {
            'page_url': 'https://f1113.wonderfulday30.live/forumdisplay.php?fid=19',
            'root_dir': r'E:\爬虫\91全部'
        },
    }

    def __init__(self, type='all', max_repeat_num=100):
        # 禁止网页加载图片，但是能正常获取图片url，提高爬取速度
        # https://stackoverflow.com/questions/28070315/python-disable-images-in-selenium-google-chromedriver/31581387#31581387
        options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        # options.add_argument("--window-size=0,0")
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=options)
        # self.driver.minimize_window()
        # self.driver = webdriver.Chrome()
        self.wait_time = 30
        self.long_wait_time = 60
        self.save_dir = r'D:\PycharmProjects\sex-spider\file'
        self.finish_file = os.path.join(self.save_dir, 'nineporn.txt')
        self.repeat_num = 0
        self.max_repeat_num = max_repeat_num
        self.proxies = {
            'http': 'http://127.0.0.1:10800',
            'https': 'https://127.0.0.1:10800',
        }
        self.home_url = 'https://f1113.wonderfulday30.live/index.php'
        self.search_url = 'https://f1113.wonderfulday30.live/search.php'
        self.type = type
        self.wait_xpath = "//span[starts-with(@id,'thread')]/a"
        self.url_list_xpath = '//span[starts-with(@id,"thread")]/a/@href'
        self.convert_type = 'zh-cn'
        type_info = self.type_dict.get(self.type)
        all_info = self.type_dict.get('all')
        self.page_url = type_info.get('page_url') or all_info.get('page_url')
        self.root_dir = type_info.get('root_dir') or all_info.get('root_dir')
        self.get_pre_process()

    def get_pre_process(self):
        res = urlparse(self.page_url)
        pre_url = res.scheme + '://' + res.netloc
        self.pre_url = pre_url
        with open(self.finish_file, 'r', encoding='utf8') as f:
            self.content = f.read()

    @count_time
    def get_url_list(self):
        try:
            self.driver.get(self.page_url)
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(self.driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, self.wait_xpath)))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            url_list = selector.xpath(self.url_list_xpath)
        except Exception as e:
            print('get_url_list失败:{}\nException:{}'.format(self.page_url, repr(e)))
            return []
        print('%s:url_list获取完成:%s' % (len(url_list), self.page_url))
        return url_list

    # @count_time
    def get_pic_list(self, detail_url):
        title = ''
        self.options.add_argument('headless')
        driver = webdriver.Chrome(options=self.options)

        try:
            # driver.maximize_window()
            # driver.minimize_window()
            driver.get(detail_url)
            # driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, self.long_wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='threadtitle']/h1")))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath("//div[@id='threadtitle']/h1/text()")[0]
            block = selector.xpath('//div[@id="threadtitle"]/../div[@class="locked"]')
            content_list = selector.xpath('//div[@id="threadtitle"]/../div[2]//text()')
            author = selector.xpath('//div[@id="postlist"]/div[1]//div[@class="postinfo"]/a/text()')[0]
            str_content = ''.join(content_list).replace(" ", '').replace("\n", '')
            if block:
                return [], '禁言-' + title
            if ('删' in title):
                return [], '标题删除-' + title
            if (len(str_content) < 100) and ('删' in str_content):
                return [], '正文删除-' + title
            if len(str_content) < 200:
                return [], '内容太短-' + title
            if author == 'admin':
                return [], '管理员贴-' + title

            wait = WebDriverWait(driver, self.long_wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, "//img[starts-with(@file,'http')]")))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            pic_url_list = selector.xpath("//img[starts-with(@file,'http')]/@file")
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            if not pic_url_list:
                title = '空列表-' + title
            return pic_url_list, title
        except Exception as e:
            print('get_pic_list失败:{}\nException:{}'.format(detail_url, repr(e)))
            return [], '失败-' + title
        finally:
            driver.quit()

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
                if status_code >= 400:
                    print("status_code:%s" % status_code)
                    print("url:%s" % url)
                    return
                headers = requests.head(url, timeout=self.long_wait_time).headers
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

    @count_time
    def download(self, detail_url):
        pic_list, title = self.get_pic_list(detail_url)
        legal_title = re.sub(r"[^\w]", "", title)
        legal_title = convert(legal_title, self.convert_type)
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

    @count_time
    def get_next_page(self):
        for i in range(5):
            try:
                self.driver.get(self.page_url)
                wait = WebDriverWait(self.driver, self.wait_time * (i + 1))
                wait.until(EC.presence_of_element_located((By.XPATH, '//a[@class="next"]')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                # selector = self.get_selector('//a[@class="next"]')
                next_page = selector.xpath('//div[@class="pages"]/a[@class="next"]/text()')
                print('next_page:%s' % next_page[0])
                next_url = selector.xpath('//a[@class="next"]/@href')[0]
                next_url = urljoin(self.pre_url, next_url)
                print('next_url:%s' % next_url)
                self.page_url = next_url
                return True
            except Exception as e:
                print('get_next_page失败:{}\nException:{}'.format(self.page_url, repr(e)))
                time.sleep((i + 1) * 10)
        return False

    def record_finish_url(self, finish_url, title):
        try:
            with open(self.finish_file, 'a', encoding='utf8') as f:
                f.write(title + '|' + finish_url + '\n')
        except Exception:
            print('写入失败：%s，标题：%s' % (finish_url, title))
            print(traceback.format_exc())

    # @count_time
    def check_repeat_url(self, url):
        try:
            query = urlsplit(url).query
            params = parse_qs(query)
            unique_str = params.get('tid')[0]
            if unique_str in self.content:
                self.repeat_num += 1
                print('repeat_num:%s' % self.repeat_num)
                print('已经下载过：%s' % (url))
                return True
        except Exception:
            print(traceback.format_exc())

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
                print(traceback.format_exc())
                print('download fail:%s' % url)
            else:
                if title:
                    self.record_finish_url(url, title)

    def search_action(self, text, type):
        self.login()
        self.driver.get(self.search_url)
        search_button = self.driver.find_element_by_xpath('//button[@id="searchsubmit"]')
        try:
            if type == 'title':
                title_input = self.driver.find_element_by_xpath('//input[@id="srchtxt"]')
                title_input.send_keys(text)
            if type == 'author':
                advanced_button = self.driver.find_element_by_xpath('//p[@class="searchkey"]/a')
                advanced_button.click()
                author_input = self.driver.find_element_by_xpath('//input[@id="srchname"]')
                author_input.send_keys(text)
            search_button.click()
            self.page_url = self.driver.current_url
        except Exception as e:
            raise e

    def get_search_url_list(self):
        try:
            self.driver.get(self.page_url)
            wait = WebDriverWait(self.driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//th[@class="subject"]/a')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            url_list = selector.xpath('//th[@class="subject"]/a/@href')
        except Exception as e:
            return []
        return url_list

    def login(self):
        try:
            self.driver.get(self.home_url)
            login_btn = self.driver.find_element_by_xpath('//div[@id="umenu"]/a[position()=2]')
            login_btn.click()
            wait = WebDriverWait(self.driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="username"]')))
            username_input = self.driver.find_element_by_xpath('//input[@name="username"]')
            password_input = self.driver.find_element_by_xpath('//input[@name="password"]')
            enter = self.driver.find_element_by_xpath('//button[@name="loginsubmit"]')
            username_input.send_keys(nineporn_username)
            password_input.send_keys(nineporn_password)
            enter.click()
        except Exception as e:
            raise e

    def download_search(self, text, type):
        self.search_action(text, type)
        while True:
            url_list = self.get_search_url_list()
            url_list = [urljoin(self.pre_url, url) for url in url_list]
            self.single_thread_download(url_list)
            next_page = self.get_next_page()
            if not next_page:
                print('最后一页:%s' % self.page_url)
                self.driver.quit()
                break

    def get_user_list(self):
        try:
            self.driver.get(self.page_url)
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(self.driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, self.wait_xpath)))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            user_list = selector.xpath('//tbody//td[@class="author"]//a/text()')
        except Exception as e:
            print('get_user_list失败:{}\nException:{}'.format(self.page_url, repr(e)))
            return []
        print('%s:get_user_list获取完成:%s' % (len(user_list), self.page_url))
        return user_list

    def get_big_user(self):
        all_user_set = set()
        print('开始下载:{}'.format(self.type))
        while True:
            user_list = self.get_user_list()
            all_user_set |= set(user_list)
            next_page = self.get_next_page()
            if not next_page:
                print('最后一页:%s' % self.page_url)
                self.driver.quit()
                break

        try:
            with open('../file/big_user.txt', 'r', encoding='utf8') as f:
                user_list = f.readlines()
                user_list = [user.strip() for user in user_list]
            all_user_set |= set(user_list)
        except FileNotFoundError:
            pass
        with open('../file/big_user.txt', 'w', encoding='utf8') as f:
            for user in all_user_set:
                f.write(user + "\n")

    @count_time
    def main(self, mutil=True):
        print('开始下载:{}'.format(self.type))
        while True:
            url_list = self.get_url_list()
            url_list = [urljoin(self.pre_url, url) for url in url_list]
            if mutil:
                self.mutil_thread_download(url_list, max_workers=10)
            else:
                self.single_thread_download(url_list)
            if self.repeat_num > self.max_repeat_num:
                print('重复帖子过多')
                self.driver.close()
                self.driver.quit()
                break
            next_page = self.get_next_page()
            if not next_page:
                print('最后一页:%s' % self.page_url)
                self.driver.quit()
                break


if __name__ == '__main__':
    gem = NinePorn('gem')
    gem.main(mutil=False)
    # all = NinePorn('all')
    # all.main(mutil=False)
    # ori = NinePorn('ori_gem')
    # ori.main()
    # ori.get_big_user()

    # np = NinePorn()
    # np.download_search(text='lvcha7777', type='author')
    # np.download_search(text='露脸', type='title')
