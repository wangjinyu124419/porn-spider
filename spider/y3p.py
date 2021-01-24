from spider.base import *


class Y3p(BasePorn):
    def __init__(self,
                 page_url='https://y3p.org/viewforum.php?f=6',
                 finish_file_name='y3p.txt',
                 root_dir=r'E:\爬虫\y3p',
                 max_repeat_num=1000,
                 wait_time=30,
                 long_wait_time=60,
                 disable_load_img=True,
                 headless=True,
                 proxies=None,
                 save_dir='../file',
                 mutil_thread=True,
                 url_list_xpath='//div[@class="list-inner"]/a/@href',
                 next_page_xpath='//li[@class="arrow next"]/a/@href'
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
            unique_str = url.split('&')[1]
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
        # self.options.add_argument("--window-size=0,0")
        driver = webdriver.Chrome(options=self.options)
        try:
            driver.get(detail_url)
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//h2[@class="topic-title"]/a')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath('//h2[@class="topic-title"]/a/text()')[0]
            wait = WebDriverWait(driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="page-body"]/div[position()=3]')))
            pic_url_list = selector.xpath('//div[@id="page-body"]/div[position()=3]//img/@src')
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            if not pic_url_list:
                title = '空列表-' + title
            return pic_url_list, title
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return [], '失败-' + title
        finally:
            driver.close()


if __name__ == '__main__':
    y3p = Y3p()
    y3p.main()
