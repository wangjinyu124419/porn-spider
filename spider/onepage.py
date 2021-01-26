from urllib.parse import urlparse, urljoin

import gevent
from gevent import monkey

gevent.monkey.patch_all(thread=False)
import os
import time
import requests
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
import re

from spider.base import count_time


class OnePage():
    def img_xpath__init__(self, img_xpath='//body//div//img/@src'):
        # 禁止网页加载图片，但是能正常获取图片url，提高爬取速度
        # https://stackoverflow.com/questions/28070315/python-disable-images-in-selenium-google-chromedriver/31581387#31581387
        options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        # options.add_argument("--window-size=0,0")
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=options)
        self.wait_time = 100
        self.proxies = {
            'http': 'http://127.0.0.1:10800',
            'https': 'https://127.0.0.1:10800',
        }
        self.root_dir = r'E:\爬虫\onepage'
        self.img_xpath = img_xpath
        self.wait_xpath = self.img_xpath.rsplit('/', maxsplit=1)[0]

    def get_pic_name(self, url):
        parse_url = urlparse(url)
        file_name = os.path.basename(parse_url.path)
        suffix = file_name.split('.')[-1]
        if suffix not in ['jpg', 'jpeg', 'png', 'gif']:
            headers = requests.head(url, proxies=self.proxies, timeout=self.wait_time).headers
            cd = headers.get('Content-Disposition')
            file_name = cd.split("''")[-1]
        return file_name

    @count_time
    def get_pic_list(self, detail_url):
        try:
            netloc = urlparse(detail_url).netloc
            scheme = urlparse(detail_url).scheme
            url_pre = scheme + '://' + netloc
            self.driver.get(detail_url)
            wait = WebDriverWait(self.driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, self.wait_xpath)))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            pic_url_list = selector.xpath(self.img_xpath)
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            fix_url_list = [urljoin(url_pre, pic_url) for pic_url in pic_url_list]
            return fix_url_list
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return [],
        finally:
            self.driver.quit()

    def get_pic_name(self, url):
        # https://www.sammyboy.com/attachments/img-20200515-wa0009-jpg.78641/
        res = re.search('/([^/]*(jpg|png|jpeg))', url)
        if not res:
            return 'temp.jpg'
        return res.group(1) + '.jpg'

    def save_pic(self, url):
        name = self.get_pic_name(url)
        pic_path = os.path.join(self.root_dir, name)
        if os.path.exists(pic_path):
            print('文件已存在:%s' % pic_path)
            return
        for i in range(5):
            try:
                status_code = requests.head(url, timeout=(i + 1) * 10, proxies=self.proxies).status_code
                if status_code != 200:
                    print("status_code:%s" % status_code)
                    print("url:%s" % url)
                    return
                content = requests.get(url, timeout=(i + 1) * 10, proxies=self.proxies).content
                with open(pic_path, 'wb') as f:
                    f.write(content)
                    print(pic_path)
                    return
            except Exception as e:
                print('保存失败第%d次，url:%s,异常信息:%s' % (i + 1, url, e))
                if i == 4:
                    print(traceback.format_exc())
                    print('save_pic失败：%s' % url)
                time.sleep(i + 1)
                continue

    @count_time
    def download(self, detail_url):
        pic_list = self.get_pic_list(detail_url)
        g_list = []
        for pic_url in pic_list:
            g_list.append(gevent.spawn(self.save_pic, pic_url))
        gevent.joinall(g_list)


if __name__ == '__main__':
    op = OnePage(img_xpath='//div[@class="entry-content"]/p[6]//img/@src')
    op.download('https://iav77.com/archives/296486')
