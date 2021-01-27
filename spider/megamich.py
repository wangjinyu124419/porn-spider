from spider.base import *
from utils.baidu_translate import baidu_tranlate


class Megamich(BasePorn):

    def __init__(self,
                 page_url='http://megamich.com',
                 root_dir=r'E:\爬虫\megamich',
                 finish_file_name='Megamich.txt',
                 max_repeat_num=100,
                 wait_time=30,
                 long_wait_time=60,
                 disable_load_img=True,
                 headless=True,
                 proxies=None,
                 save_dir=os.path.join(base_dir, 'file'),
                 mutil_thread=True,
                 url_list_xpath='//ul[@class="list-normal"]/li//h3/a/@href',
                 next_page_xpath='//a[@class="next page-numbers"]/@href',
                 max_workers=5
                 ):
        super().__init__(
            page_url,
            root_dir=root_dir,
            finish_file_name=finish_file_name,
            max_repeat_num=max_repeat_num,
            wait_time=wait_time,
            long_wait_time=long_wait_time,
            disable_load_img=disable_load_img,
            headless=headless,
            proxies=proxies,
            save_dir=save_dir,
            mutil_thread=mutil_thread,
            url_list_xpath=url_list_xpath,
            next_page_xpath=next_page_xpath,
            max_workers=max_workers
        )

    def get_pic_list(self, detail_url):
        title = ''
        # self.options.add_argument('headless')
        driver = webdriver.Chrome(options=self.options)
        try:
            # driver.maximize_window()
            driver.get(detail_url)
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div/h1")))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath("//div/h1/text()")[0]
            wait = WebDriverWait(driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//img[starts-with(@src,"/wp-content/uploads/img")]')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            pic_url_list = selector.xpath('//img[starts-with(@src,"/wp-content/uploads/img")]/@src')
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            return True, pic_url_list, title
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return False, [], title
        finally:
            driver.quit()

    @count_time
    def download(self, detail_url):
        success, pic_list, title = self.get_pic_list(detail_url)
        legal_title = re.sub(r"[^\w]", "", title)
        legal_title = convert(legal_title, self.convert_type)
        tranlate_title = baidu_tranlate(legal_title)
        tranlate_title = re.sub(r"[^\w]", "", tranlate_title)
        legal_title = (tranlate_title + '_____' + legal_title)[:100]
        if not tranlate_title:
            return '翻译失败-' + legal_title
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


if __name__ == '__main__':
    mg = Megamich()
    mg.main()
