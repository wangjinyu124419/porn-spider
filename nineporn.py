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

class NinePorn():
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    def __init__(self,type=None):
        #禁止网页加载图片，但是能正常获取图片url，提高爬取速度
        #https://stackoverflow.com/questions/28070315/python-disable-images-in-selenium-google-chromedriver/31581387#31581387
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('headless')
        chrome_options.add_argument("--window-size=0,0")

        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        self.driver.minimize_window()
        # self.driver = webdriver.Chrome()
        self.url_list_time = 30
        self.pic_list_time = 30
        self.title_time= 30
        self.next_page_time = 60
        self.login_time = 60
        self.pre_url = 'https://f.wonderfulday28.live/'
        self.finish_file = 'nineporn.txt'
        self.proxies = {
            'http': 'http://127.0.0.1:1080',
            'https': 'https://127.0.0.1:1080',
        }
        if type=='gem':
            print('下载精华帖')
            self.page_url = 'https://f.wonderfulday28.live/forumdisplay.php?fid=19&filter=digest&page=1'
            self.root_dir = r'K:\爬虫\91精华'
        elif type=='hot':
            print('下载热门贴')
            self.page_url = 'https://f.wonderfulday28.live/forumdisplay.php?fid=19&orderby=dateline&filter=7948800'
            self.root_dir = r'K:\爬虫\91热门'

        elif type=='all':
            print('下载全部帖子')
            self.page_url = 'https://f.wonderfulday28.live/forumdisplay.php?fid=19'
            self.root_dir = r'K:\爬虫\91全部'
        else:
            print('下载全部帖子')
            self.page_url = 'https://f.wonderfulday28.live/forumdisplay.php?fid=19'
            self.root_dir = r'K:\爬虫\91全部'

    @count_time
    def get_url_list(self):
        try:
            self.driver.get(self.page_url)
            wait = WebDriverWait(self.driver, 30)
            wait.until(EC.presence_of_element_located((By.XPATH, "//span[starts-with(@id,'thread')]/a")))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            url_list = selector.xpath("//span[starts-with(@id,'thread')]/a/@href")
        except Exception:
            print(traceback.format_exc())
            return []
        print('%s:url_list获取完成:%s'%(len(url_list),self.page_url))
        return url_list

    @count_time
    def get_pic_list(self, detail_url):
        title = ''
        self.chrome_options.add_argument('headless')
        driver = webdriver.Chrome(chrome_options=self.chrome_options)

        try:
            # driver.maximize_window()
            driver.minimize_window()
            driver.get(detail_url)
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, self.title_time)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='threadtitle']/h1")))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath("//div[@id='threadtitle']/h1/text()")[0]
            block = selector.xpath('//div[@id="threadtitle"]/../div[@class="locked"]')
            content_list = selector.xpath('//div[@id="threadtitle"]/../div[2]//text()')
            author = selector.xpath('//div[@id="postlist"]/div[1]//div[@class="postinfo"]/a/text()')[0]
            str_content=''.join(content_list).replace(" ",'').replace("\n",'')
            if block:
                return [],'禁言-'+title
            if ('删' in title) :
                return [],'标题删除-'+title
            if (len(str_content)<100) and('删' in str_content) :
                return [],'正文删除-'+title
            # if 'attach' in str_content:
            #     return [],'attach-'+title
            if len(str_content)<200:
                # print('内容太短:%s:%s'%(str_content,detail_url))c
                return [],'内容太短-'+title
            if author=='admin':
                return [],'管理员贴-'+title

            wait = WebDriverWait(driver, self.pic_list_time)
            wait.until(EC.presence_of_element_located((By.XPATH, "//img[starts-with(@file,'attachments')]")))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            pic_url_list = selector.xpath("//img[starts-with(@file,'attachments')]/@file")
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            pic_url_list=[self.pre_url+pic_url for pic_url in pic_url_list]
            return pic_url_list, title
        except Exception:
            print('get_pic_list失败：%s'%detail_url)
            print(traceback.format_exc())
            return [],'失败-' + title
        finally:
            driver.close()

    def save_pic(self, url, path):
        name = url.split('/')[-1]
        pic_path = os.path.join(self.root_dir, path, name)
        if os.path.exists(pic_path):
            print('文件已存在:%s' % pic_path)
            return
        for i in range(5):
            try:
                status_code = requests.get(url,timeout=(i+1)*10).status_code
                if status_code != 200:
                    print("status_code:%s" % status_code)
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
        pic_list, title = self.get_pic_list(detail_url)
        if not pic_list:
            print('pic_list为空-%s:%s'%(title,detail_url))
            self.record_finish_url(detail_url,title)
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
                wait = WebDriverWait(self.driver, self.next_page_time*(i+1))
                wait.until(EC.presence_of_element_located((By.XPATH, '//a[@class="next"]')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                next_page = selector.xpath('//div[@class="pages"]/a[@class="next"]/text()')
                print('next_page:%s' % next_page[0])
                next_url = self.pre_url + selector.xpath('//a[@class="next"]/@href')[0]
                print('next_url:%s' % next_url)
                self.page_url = next_url
                return True
            except Exception:
                print(traceback.format_exc())
                time.sleep(i*10)
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
            tran_url=url.split("&")[0]
            with open(self.finish_file, 'r', encoding='utf8') as f:
                content_list = f.readlines()
                for  content in content_list:
                    if tran_url in content:
                        print('已经下载过：%s' % (content.strip()))
                        return True
        except Exception:
            print(traceback.format_exc())

    @count_time
    def main(self):
        while True:
            url_list = self.get_url_list()
            with ThreadPoolExecutor(max_workers=10) as executor:
            # with ThreadPoolExecutor() as executor:
                t_dict = {executor.submit(self.download, self.pre_url+pic_t): pic_t for pic_t in url_list if
                          not self.check_repeat_url(self.pre_url+pic_t)}
                for future in as_completed(t_dict):
                    url = t_dict[future]
                    try:
                        title=future.result()
                    except Exception:
                        print('download异常:%s' % url + '\n', traceback.format_exc())
                    else:
                        if title:
                                self.record_finish_url(self.pre_url+url, title)
            # for url in url_list:
            #     full_url = self.pre_url + url
            #     if self.check_repeat_url(full_url):
            #         continue
            #     try:
            #         title = self.download(full_url)
            #     except Exception:
            #         print(traceback.format_exc())
            #         print('download fail:%s' % full_url)
            #     else:
            #         if title:
            #             self.record_finish_url(full_url, title)
            next_page = self.get_next_page()
            if not next_page:
                print('最后一页:%s'%self.page_url)
                self.driver.close()
                break


if __name__ == '__main__':
    gem = NinePorn('gem')
    gem.main()
    hot = NinePorn('hot')
    hot.main()
    all = NinePorn('all')
    all.main()
