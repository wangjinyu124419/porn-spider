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
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
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

class OnePage():
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    def __init__(self,url=None):
        #禁止网页加载图片，但是能正常获取图片url，提高爬取速度
        #https://stackoverflow.com/questions/28070315/python-disable-images-in-selenium-google-chromedriver/31581387#31581387
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('headless')
        # chrome_options.add_argument("--window-size=0,0")

        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        # self.driver.minimize_window()
        # self.driver = webdriver.Chrome()
        self.url_list_time = 30
        self.pic_list_time = 30
        self.title_time= 30
        self.next_page_time = 60
        self.login_time = 60
        self.pre_url = 'https://f.wonderfulday28.live/'
        self.finish_file = 'nineporn.txt'
        self.page_url=url
        self.proxies = {
            'http': 'http://127.0.0.1:1080',
            'https': 'https://127.0.0.1:1080',
        }

        self.root_dir = r'K:\爬虫\onepage'

    @count_time
    def get_pic_list(self, detail_url):
        self.chrome_options.add_argument('headless')
        driver = webdriver.Chrome(chrome_options=self.chrome_options)
        try:
            # driver.maximize_window()
            driver.minimize_window()
            driver.get(detail_url)
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, self.pic_list_time)
            wait.until(EC.presence_of_element_located((By.XPATH, "//img")))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            pic_url_list = selector.xpath("//img/@src")
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            fix_url_list = [pic_url for pic_url in pic_url_list if pic_url.startswith('http')]
            return fix_url_list
        except Exception:
            print('get_pic_list失败：%s'%detail_url)
            print(traceback.format_exc())
            return [],
        finally:
            driver.close()

    def save_pic(self, url):
        pic_url = url.split('?')[0]
        name=pic_url.split('/')[-1]
        pic_path = os.path.join(self.root_dir, name)
        if os.path.exists(pic_path):
            print('文件已存在:%s' % pic_path)
            return
        for i in range(5):
            try:
                status_code = requests.get(url,timeout=(i+1)*10,proxies=self.proxies).status_code
                if status_code != 200:
                    print("status_code:%s" % status_code)
                    print("url:%s" % url)
                    return
                content = requests.get(url,timeout=(i+1)*10).content
                with open(pic_path, 'wb') as f:
                    f.write(content)
                    print(pic_path)
                    return
            except Exception as e:
                print('保存失败第%d次，url:%s,异常信息:%s'%(i+1,url,e))
                if i==4:
                    print(traceback.format_exc())
                    print('save_pic失败：%s' % url)
                time.sleep(i)
                continue


    @count_time
    def download(self, detail_url):
        pic_list = self.get_pic_list(detail_url)
        g_list = []
        for pic_url in pic_list:
            g_list.append(gevent.spawn(self.save_pic, pic_url))
        gevent.joinall(g_list)


if __name__ == '__main__':
    op=OnePage()
    op.download('https://dark.fun1shot.com/article/17509')


