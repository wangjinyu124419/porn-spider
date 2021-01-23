from spider.nineporn import *


class Y3p(NinePorn):
    def __init__(self):
        super().__init__()
        self.finish_file = os.path.join(self.save_dir, 'y3p.txt')
        self.page_url = 'https://y3p.org/viewforum.php?f=6'
        self.root_dir = r'E:\爬虫\y3p'
        self.get_pre_process()
        self.wait_xpath = '//div[@class="list-inner"]/a'
        self.url_list_xpath = '//div[@class="list-inner"]/a/@href'

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
            wait = WebDriverWait(driver, self.title_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//h2[@class="topic-title"]/a')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath('//h2[@class="topic-title"]/a/text()')[0]
            wait = WebDriverWait(driver, self.pic_list_time)
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

    def get_next_page(self):
        for i in range(5):
            try:
                self.driver.get(self.page_url)
                wait = WebDriverWait(self.driver, self.next_page_time * (i + 1))
                wait.until(EC.presence_of_element_located((By.XPATH, '//li[@class="arrow next"]/a')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                next_url = selector.xpath('//li[@class="arrow next"]/a/@href')[0]
                next_url = urljoin(self.pre_url, next_url)
                print('next_url:%s' % next_url)
                self.page_url = next_url
                return next_url
            except Exception:
                print('获取下一页失败：%s' % self.page_url)
                print(traceback.format_exc())
                continue


if __name__ == '__main__':
    y3p = Y3p()
    y3p.main(mutil=True)
