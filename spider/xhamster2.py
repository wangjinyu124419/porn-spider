import json
from math import ceil

import gevent
from gevent import monkey

gevent.monkey.patch_all()

import os
import time
import shutil

import requests
from lxml import etree
from xml.etree.ElementTree import tostring
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import traceback
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def count_time(fun):
    def warpper(*args, **kwargs):
        s_time = time.time()
        res = fun(*args, **kwargs)
        e_time = time.time()
        t_time = e_time - s_time
        print('%s耗时：%s,args:%s' % (fun.__name__, t_time, args))
        return res

    return warpper


class Xhamster():
    def __init__(self, username=None):
        # 禁止网页加载图片，但是能正常获取图片url，提高爬取速度
        # https://stackoverflow.com/questions/28070315/python-disable-images-in-selenium-google-chromedriver/31581387#31581387
        self.options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        # options.add_argument("--window-size=0,0")

        # prefs = {"profile.managed_default_content_settings.images": 2}
        # self.options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.minimize_window()
        self.username = username
        # self.driver = webdriver.Chrome()
        self.wait_time = 60
        self.pic_list_time = 60
        self.title_time = 60
        self.next_page_time = 30
        self.login_time = 60
        self.pre_url = 'https://xhamster15.com'
        self.finish_file = os.path.join(base_dir, 'file', 'xhamster2.txt')
        self.cookie_path = os.path.join(base_dir, 'file', 'xhamster2_cookie.txt')

        self.proxies = {
            # 'http': 'http://127.0.0.1:10800',
            # 'https': 'https://127.0.0.1:10800',
        }

        self.base_url = 'https://xhamster15.com/users/{}/photos'
        self.page_url = self.base_url.format(username)
        self.root_dir = r'E:\爬虫\xhamster2'
        self.user_list = ['nuvolari2018']
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}

    @count_time
    def get_url_list(self):
        try:
            self.driver.get(self.page_url)
            self.set_cookies(self.driver)
            wait = WebDriverWait(self.driver, 60)
            wait.until(EC.presence_of_element_located(
                (By.XPATH, '//a[@class="gallery-thumb__link thumb-image-container role-pop"]/img')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            url_list = selector.xpath('//a[@class="gallery-thumb__link thumb-image-container role-pop"]/img/../@href')
            print('%s:get_url_list获取完成:%s' % (len(url_list), self.page_url))
            return url_list
        except Exception:
            print(traceback.format_exc())
            time.sleep(self.wait_time)
            return []

    @count_time
    def get_pic_list(self, detail_url):
        title = ''
        # self.options.add_argument('headless')
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

    def get_pic_url_list(self, detail_url):
        all_pic_url_list = []
        try:
            page_source = requests.get(detail_url, timeout=self.wait_time, proxies=self.proxies).content
            selector = etree.HTML(page_source)
            pic_num = int(selector.xpath('//span[@class="page-title__count"]/text()')[0])
            page_num = ceil(pic_num / 60)
        except Exception as e:
            print('get_page_num失败:{},url:{}'.format(e, detail_url))
            return False, all_pic_url_list, 0
        else:
            for i in range(1, page_num + 1):
                page_detail_url = detail_url + '/' + str(i)
                try:
                    page_source = requests.get(page_detail_url, timeout=self.wait_time, proxies=self.proxies).content
                    selector = etree.HTML(page_source)
                    pic_url_list = selector.xpath('//div[@id="photo-slider"]//a[starts-with(@id,"photo")]/@href')
                    all_pic_url_list.extend(pic_url_list)
                except Exception as e:
                    print('get_pic_url_list失败:{},url:{}'.format(e, page_detail_url))
                    print(traceback.format_exc())
                    return False, all_pic_url_list, pic_num
            return True, all_pic_url_list, pic_num

    @count_time
    def get_large_pic_list(self, detail_url):
        self.options.add_argument('headless')
        driver = webdriver.Chrome(options=self.options)
        pic_url_list = []
        total_num = 0
        try:
            driver.get(detail_url)
            self.set_cookies(driver)
            wait = WebDriverWait(driver, self.title_time)
            # wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="mixed-list"]/a')))
            wait.until(EC.presence_of_element_located((By.XPATH, '//script[@id="initials-script"]')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            while True:
                page_source = driver.page_source
                selector = etree.HTML(page_source)
                wait.until(EC.presence_of_element_located((By.XPATH, '//img[@class="fotorama__img"]')))
                pic_url = selector.xpath('//img[@class="fotorama__img"]/@src')
                if not pic_url:
                    self.driver.refresh()
                    continue
                pic_url_list.extend(pic_url)
                wait.until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="photo-amounts-info bg-substrate"]')))
                page_source = driver.page_source
                selector = etree.HTML(page_source)
                pic_num = selector.xpath('//div[@class="photo-amounts-info bg-substrate"]/text()')[0]
                cur_num = int(pic_num.split('/')[0])
                total_num = int(pic_num.split('/')[1])
                if cur_num == total_num:
                    return True, list(set(pic_url_list)), total_num
                # ActionChains(driver).move_to_element(pic_box).perform()
                # pic_box = driver.find_element_by_xpath('//div[@id="photo_slider"]')
                wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="photo_slider"]')))
                next_pic = driver.find_element_by_xpath('//div[@id="photo_slider"]')
                size = next_pic.size
                w, h = size['width'], size['height']
                actions = ActionChains(driver)
                actions.move_to_element_with_offset(next_pic, w * 0.8, h * 0.8).click().perform()
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return False, list(set(pic_url_list)), total_num
        finally:
            driver.quit()

    # @count_time
    # def get_pic_list(self, all_pic_page_list):
    #     # self.options.add_argument('headless')
    #     driver = webdriver.Chrome(options=self.options)
    #     large_pic_url_list = []
    #     for url in all_pic_page_list:
    #         try:
    #             driver.get(url)
    #             wait = WebDriverWait(driver, self.pic_list_time)
    #             wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"fotorama__active")]/img')))
    #             page_source = driver.page_source
    #             selector = etree.HTML(page_source)
    #             large_img_url = selector.xpath('//div[contains(@class,"fotorama__active")]/img/@src')[0]
    #         except Exception as e:
    #             print('get large_img_url fail:%s execept:%s' % (url, e))
    #         else:
    #             large_pic_url_list.append(large_img_url)
    #     driver.close()
    #     return large_pic_url_list

    def save_pic(self, url, path):
        name = url.split('/')[4] + '.jpg'
        pic_path = os.path.join(path, name)
        if os.path.exists(pic_path):
            print('文件已存在:%s' % pic_path)
            return
        for i in range(1, 6):
            try:
                status_code = requests.get(url, timeout=i * 10).status_code
                if status_code != 200:
                    print("status_code:%s" % status_code)
                    return
                content = requests.get(url, timeout=i * 10).content
                with open(pic_path, 'wb') as f:
                    f.write(content)
                    print(pic_path)
                    return
            except Exception as e:
                # print('保存失败第%d次，url:%s,异常信息:%s' % (i, url, e))
                if i == 5:
                    print(traceback.format_exc())
                    print('save_pic失败：%s' % url)
                time.sleep(i)
                continue

    @count_time
    def download(self, detail_url):
        print('开始下载:%s' % detail_url)
        success, pic_list, pic_num = self.get_pic_url_list(detail_url)
        legal_title = detail_url.split('/')[-1]
        legal_title = legal_title + '_' + str(pic_num) + 'P'
        # legal_title = re.sub(r"[^\w-]", "", title)
        if not success:
            print('pic_num 失败:{}'.format(detail_url))
            legal_title = '失败-' + legal_title
            return legal_title

        if pic_num < 10:
            print('pic_num 太少:{}'.format(detail_url))
            return legal_title
        if pic_num != len(pic_list):
            legal_title = '数量不符-' + legal_title
            print('图片数量不符，pic_num:{},pic_list:{}'.format(pic_num, len(pic_list)))
        path = os.path.join(self.root_dir, self.username, legal_title)
        if not os.path.exists(path):
            os.makedirs(path)
        g_list = []
        for pic_url in pic_list:
            g_list.append(gevent.spawn(self.save_pic, pic_url, path))
        gevent.joinall(g_list)
        download_num = len(os.listdir(path))
        if download_num != len(pic_list):
            legal_title = '下载缺失-' + legal_title
            print('下载缺失，download_num:{},pic_list:{}'.format(download_num, len(pic_list)))
        return legal_title

    @count_time
    def get_next_page(self):
        for i in range(3):
            try:
                self.driver.get(self.page_url)
                wait = WebDriverWait(self.driver, self.next_page_time)
                wait.until(EC.presence_of_element_located((By.XPATH, '//li[@class="next"]/a')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                next_url = selector.xpath('//li[@class="next"]/a/@href')[0]
                print('next_url:%s' % next_url)
                self.page_url = next_url
                return True
            except Exception:
                print(traceback.format_exc())
                if i < 2:
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
            tran_url = url.split("-")[-1]
            with open(self.finish_file, 'r', encoding='utf8') as f:
                content_list = f.readlines()
                for content in content_list:
                    if tran_url in content:
                        print('已经下载过：%s' % (content.strip()))
                        return True
        except Exception:
            print(traceback.format_exc())

    def save_cookie(self, url):
        self.driver.get(url)
        cookies = self.driver.get_cookies()
        with open(self.cookie_path, 'w', encoding='utf8') as f:
            cookies_json = json.dumps(cookies)
            f.write(cookies_json)

    def set_cookies(self, driver):
        # 设置cookie前需要先打开网页
        with open(self.cookie_path, encoding='utf8') as f:
            cookies_json = f.read()
            cookies = json.loads(cookies_json)
        for cookie in cookies:
            driver.add_cookie(cookie)
        # 设置cookie后需要刷新网页，显示登录效果
        driver.refresh()

    def one_user(self, username):
        self.username = username
        page_url = self.base_url.format(username)
        page_source = requests.get(page_url, timeout=self.wait_time, proxies=self.proxies).content
        selector = etree.HTML(page_source)
        galleriy_num = int(selector.xpath('//h1[@class="current-tab button"]//span/text()')[0])
        galleriy_page_num = ceil(galleriy_num / 30)
        for i in range(1, galleriy_page_num + 1):
            print('用户:{}第几页:{}'.format(username, i))
            self.page_url = page_url + "/" + str(i)
            url_list = self.get_url_list()
            with ThreadPoolExecutor() as executor:
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

    def mutil_user(self):
        for user in self.user_list:
            print('开始下载用户:{}'.format(user))
            self.one_user(user)
        self.driver.quit()

    def rename(self):
        print('开始爬取:{}'.format(self.page_url))
        for user in self.user_list:
            self.username = user
            self.page_url = self.base_url.format(user)
            while True:
                try:
                    self.driver.get(self.page_url)
                    wait = WebDriverWait(self.driver, self.wait_time)
                    wait.until(EC.presence_of_element_located(
                        (By.XPATH, '//div[@class="thumb-list thumb-list--gallery-full-width"]/div')))
                    page_source = self.driver.page_source
                    selector = etree.HTML(page_source)
                    post_list = selector.xpath('//div[@class="thumb-list thumb-list--gallery-full-width"]/div')
                    for post in post_list:
                        post = tostring(post)
                        selector = etree.HTML(post)
                        url = selector.xpath('//a[@class="gallery-thumb__link thumb-image-container role-pop"]/@href')[
                            0]
                        # title = selector.xpath('//div[@class="gallery-thumb-info__name"]/text()')[0]
                        pic_num = selector.xpath(
                            '//span[@class="gallery-thumb-info__quantity"]/span[@data-role="counter"]/text()')[0]
                        old_title = url.split('/')[-1]
                        new_title = old_title + '_' + pic_num + 'P'
                        save_path = os.path.join(self.root_dir, self.username, old_title)
                        rename_save_path = os.path.join(self.root_dir, self.username, new_title)
                        if os.path.exists(save_path):
                            print(rename_save_path)
                            try:
                                os.rename(save_path, rename_save_path)
                            except FileExistsError:
                                shutil.rmtree(save_path)
                                print(save_path, rename_save_path)
                except Exception as e:
                    print(e)

                next_page = self.get_next_page()
                if not next_page:
                    print('最后一页:%s' % self.page_url)
                    break
            print('结束爬取:{}'.format(self.username))
        self.driver.quit()


if __name__ == '__main__':
    xhamster = Xhamster()
    xhamster.mutil_user()
