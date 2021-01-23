import gevent
from gevent import monkey

gevent.monkey.patch_all()
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
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed


def count_time(fun):
    def warpper(*args):
        s_time = time.time()
        res = fun(*args)
        e_time = time.time()
        t_time = e_time - s_time
        print('%s耗时：%s' % (fun.__name__, t_time))
        return res

    return warpper


class Xhamster():
    options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    def __init__(self, username, type=None, ):
        # 禁止网页加载图片，但是能正常获取图片url，提高爬取速度
        # https://stackoverflow.com/questions/28070315/python-disable-images-in-selenium-google-chromedriver/31581387#31581387
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        # options.add_argument("--window-size=0,0")

        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=options)
        self.driver.minimize_window()
        # self.driver = webdriver.Chrome()
        self.url_list_time = 60
        self.pic_list_time = 60
        self.title_time = 60
        self.next_page_time = 60
        self.login_time = 60
        self.pre_url = 'https://xhamster2.com'
        self.finish_file = 'xhamster2.txt'
        self.proxies = {
            'http': 'http://127.0.0.1:1080',
            'https': 'https://127.0.0.1:1080',
        }

        self.page_url = 'https://xhamster2.com/users/{}/photos'.format(username)
        self.root_dir = r'E:\爬虫\xhamster2'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}

    @count_time
    def get_url_list(self):
        try:
            self.driver.get(self.page_url)
            wait = WebDriverWait(self.driver, 60)
            wait.until(EC.presence_of_element_located(
                (By.XPATH, '//a[@class="gallery-thumb__link thumb-image-container role-pop"]/img')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            url_list = selector.xpath('//a[@class="gallery-thumb__link thumb-image-container role-pop"]/img/../@href')
        except Exception:
            print(traceback.format_exc())
            return []

        print('%s:url_list获取完成:%s' % (len(url_list), self.page_url))
        return url_list

    @count_time
    def get_pic_list(self, detail_url):
        title = ''
        self.options.add_argument('headless')
        driver = webdriver.Chrome(options=self.options)
        # driver = webdriver.Chrome()

        try:
            # driver.maximize_window()
            driver.minimize_window()
            driver.get(detail_url)
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, self.title_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//div/h1')))
            wait.until(EC.presence_of_element_located((By.XPATH, '//span[@class="page-title__count"]')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath('//div/h1/text()')[0]
            img_count = selector.xpath('//span[@class="page-title__count"]/text()')[0]
            fix_title = title + '_' + img_count + 'P'

            wait = WebDriverWait(driver, self.pic_list_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//a[@class="photo-container photo-thumb role-pop"]')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            pic_url_list = selector.xpath('//a[@class="photo-container photo-thumb role-pop"]/@href')
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            # pic_url_list=[self.pre_url+pic_url for pic_url in pic_url_list]
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return [], '失败-' + title
        else:
            if len(pic_url_list) < 10:
                print('图片过少:{}'.format(detail_url))
                return [], title
            large_pic_url_list = []
            for url in pic_url_list:
                try:
                    driver.get(url)
                    wait = WebDriverWait(driver, self.pic_list_time)
                    wait.until(
                        EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"fotorama__active")]/img')))
                    # page_source = requests.get(url,headers=self.headers,timeout=60).text
                    page_source = driver.page_source
                    selector = etree.HTML(page_source)
                    large_img_url = selector.xpath('//div[contains(@class,"fotorama__active")]/img/@src')[0]
                except Exception as e:
                    print('get large_img_url fail:%s execept:%s' % (url, e))
                else:
                    large_pic_url_list.append(large_img_url)
            return large_pic_url_list, fix_title
        finally:
            driver.close()

    def save_pic(self, url, path):
        name = url.split('/')[4] + '.jpg'
        pic_path = os.path.join(self.root_dir, path, name)
        if os.path.exists(pic_path):
            print('文件已存在:%s' % pic_path)
            return
        for i in range(5):
            try:
                status_code = requests.get(url, timeout=(i + 1) * 10).status_code
                if status_code != 200:
                    print("status_code:%s" % status_code)
                    return
                content = requests.get(url, timeout=(i + 1) * 10).content
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

        if not pic_list:
            print('pic_list为空-%s:%s' % (title, detail_url))
            self.record_finish_url(detail_url, title)
            return
        print('开始下载:%s' % detail_url)

        legal_title = re.sub(r"[\/\\\:\*\?\"\<\>\|!！\.\s]", "", title)
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
        for i in range(3):
            try:
                self.driver.get(self.page_url)
                wait = WebDriverWait(self.driver, self.next_page_time * (i + 1))
                wait.until(EC.presence_of_element_located((By.XPATH, '//li[@class="next"]/a')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                # next_page = selector.xpath('//div[@class="pages"]/a[@class="next"]/text()')
                # print('next_page:%s' % next_page[0])
                next_url = selector.xpath('//li[@class="next"]/a/@href')[0]
                print('next_url:%s' % next_url)
                self.page_url = next_url
                return True
            except Exception:
                print(traceback.format_exc())
                time.sleep(i * 10)
                continue
        return False

    def record_finish_url(self, finish_url, title):
        try:
            with open(self.finish_file, 'a', encoding='utf8') as f:
                f.write(title + '|' + finish_url + '\n')
        except Exception:
            print('写入失败：%s，标题：%s' % (finish_url, title))
            print(traceback.format_exc())

    def check_repeat_url(self, url):
        try:
            tran_url = url.split("&")[0]
            with open(self.finish_file, 'r', encoding='utf8') as f:
                content_list = f.readlines()
                for content in content_list:
                    if tran_url in content:
                        print('已经下载过：%s' % (content.strip()))
                        return True
        except Exception:
            print(traceback.format_exc())

    @count_time
    def main(self):
        while True:
            url_list = self.get_url_list()
            with ThreadPoolExecutor(max_workers=5) as executor:
                t_dict = {executor.submit(self.download, pic_t): pic_t for pic_t in url_list if
                          not self.check_repeat_url(pic_t)}
                for future in as_completed(t_dict):
                    url = t_dict[future]
                    try:
                        title = future.result()
                    except Exception:
                        print('download异常:%s' % url + '\n', traceback.format_exc())
                    else:
                        if title:
                            self.record_finish_url(url, title)

            next_page = self.get_next_page()
            if not next_page:
                print('最后一页:%s' % self.page_url)
                self.driver.close()
                break


if __name__ == '__main__':
    xhamster = Xhamster('nuvo7')
    xhamster.main()
    # xhamster.download('https://fr.xhamster15.com/photos/gallery/chinese-amateur-girl552-9534722')
