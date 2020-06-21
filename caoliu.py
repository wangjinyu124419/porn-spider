from nineporn import *


class CaoLiu(NinePorn):

    def __init__(self):
        super().__init__()
        self.root_dir = r'K:\爬虫\1024'
        self.page_url = 'http://t66y.com/thread0806.php?fid=16&search=&page=1'
        self.pre_url = 'http://t66y.com/'
        self.finish_file = 'caoliu.txt'

    # @count_time
    def get_url_list(self):
        try:
            self.driver.get(self.page_url)
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(self.driver, self.url_list_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//tbody/tr[position()>11]/td[2]/h3/a')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            url_list = selector.xpath("//tbody/tr[position()>11]/td[2]/h3/a/@href")
            fix_url_list = [ url if url.startswith('http') else self.pre_url+url  for url in url_list]

        except Exception:
            print(traceback.format_exc())
            return []
        print('url_list获取完成:%s' % self.page_url)
        return fix_url_list

    # @count_time
    def get_pic_list(self, detail_url):
        title = ''
        self.chrome_options.add_argument('headless')
        self.chrome_options.add_argument("--window-size=0,0")

        driver = webdriver.Chrome(chrome_options=self.chrome_options)
        try:
            driver.get(detail_url)
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, self.title_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div[2]/table/tbody/tr/td')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath("//h4/text()")[0]
            wait = WebDriverWait(driver, self.pic_list_time)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='tpc_content do_not_catch']")))
            pic_url_list = selector.xpath("//div[@class='tpc_content do_not_catch']//@src")
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            fix_pic_url_list = [ pic_url if pic_url.startswith('http') else self.pre_url+pic_url  for pic_url in pic_url_list]

            if not pic_url_list:
                title = '空列表-' + title
            return fix_pic_url_list, title
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return [], '失败-' + title
        finally:
            driver.close()

    # @count_time
    def get_next_page(self):
        for i in range(5):
            try:
                self.driver.get(self.page_url)
                wait = WebDriverWait(self.driver, self.next_page_time*(i+1))
                wait.until(EC.presence_of_element_located((By.XPATH, '//a[text()="下一頁"]')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                next_page = selector.xpath('//a[text()="下一頁"]/text()')
                print('next_page:%s' % next_page[0])
                next_url = self.pre_url + selector.xpath('//a[text()="下一頁"]/@href')[0]
                print('next_url:%s' % next_url)
                self.page_url = next_url
                return next_url
            except Exception:
                print('获取下一页失败：%s' % self.page_url)
                print(traceback.format_exc())
                continue

    # def check_repeat_url(self, url):
    #     try:
    #         # unique_key=url.split("/")[-1]
    #         unique_key = re.match('.*(\d{7}).*', url).group(1)
    #         with open(self.finish_file, 'r', encoding='utf8') as f:
    #             content_list = f.readlines()
    #             for content in content_list:
    #                 if unique_key in content:
    #                     self.repeat_num += 1
    #                     print('repeat_num')
    #                     print('已经下载过：%s' % (content.strip()))
    #                     return True
    #     except Exception:
    #         print(traceback.format_exc())


if __name__ == '__main__':
    caoliu = CaoLiu()
    caoliu.main()
