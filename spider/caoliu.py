from spider.base import *


class CaoLiu(BasePorn):

    def __init__(self,
                 page_url='http://t66y.com/thread0806.php?fid=16&search=&page=1',
                 root_dir=r'E:\爬虫\1024',
                 finish_file_name='caoliu.txt',
                 max_repeat_num=1000,
                 wait_time=30,
                 long_wait_time=60,
                 disable_load_img=True,
                 headless=True,
                 proxies=None,
                 save_dir='../file',
                 mutil_thread=True,
                 url_list_xpath='//tbody/tr[position()>11]/td[2]/h3/a/@href',
                 next_page_xpath='//a[text()="下一頁"]/@href',
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
        )

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

    def get_pic_list(self, detail_url):
        title = ''
        self.options.add_argument('headless')
        self.options.add_argument("--window-size=0,0")
        driver = webdriver.Chrome(options=self.options)
        try:
            driver.get(detail_url)
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, self.long_wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div[2]/table/tbody/tr/td')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath("//h4/text()")[0]
            wait = WebDriverWait(driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='tpc_content do_not_catch']")))
            pic_url_list = selector.xpath("//div[@class='tpc_content do_not_catch']//@src")
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            fix_pic_url_list = [urljoin(self.pre_url, pic_url) for pic_url in pic_url_list]
            if not pic_url_list:
                title = '空列表-' + title
            return fix_pic_url_list, title
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return [], '失败-' + title
        finally:
            driver.close()


if __name__ == '__main__':
    caoliu = CaoLiu(mutil_thread=True)
    caoliu.main()
