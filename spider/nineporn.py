from urllib.parse import urlsplit, parse_qs

from spider.base import *


class NinePorn(BasePorn):
    type_dict = {
        'gem': {
            'page_url': 'https://f1113.wonderfulday30.live/forumdisplay.php?fid=19&filter=digest',
            'root_dir': r'E:\爬虫\91精华'
        },
        'ori_gem': {
            'page_url': 'https://f1113.wonderfulday30.live/forumdisplay.php?fid=4&filter=digest',
            'root_dir': r'E:\爬虫\91原创精华'
        },
        'ori': {
            'page_url': 'https://f1113.wonderfulday30.live/forumdisplay.php?fid=4',
            'root_dir': r'E:\爬虫\91原创'
        },
        'all': {
            'page_url': 'https://f1113.wonderfulday30.live/forumdisplay.php?fid=19',
            # 'page_url': 'https://f.wonderfulday25.live/forumdisplay.php?fid=19',
            # 'page_url': 'https://f1113.wonderfulday30.live/forumdisplay.php?fid=4&page=10',
            'root_dir': r'E:\爬虫\91全部'
        },
    }

    def __init__(self,
                 category,
                 finish_file_name='nineporn.txt',
                 max_repeat_num=1000,
                 wait_time=30,
                 long_wait_time=60,
                 disable_load_img=True,
                 headless=True,
                 proxies=None,
                 save_dir='../file',
                 mutil_thread=True,
                 url_list_xpath='//span[starts-with(@id,"thread")]/a/@href',
                 next_page_xpath='//a[@class="next"]/@href'
                 ):
        all_info = self.type_dict.get('all')
        type_info = self.type_dict.get(category)
        page_url = type_info.get('page_url') or all_info.get('page_url')
        root_dir = type_info.get('root_dir') or all_info.get('root_dir')
        self.home_url = 'https://f1113.wonderfulday30.live/index.php'
        self.search_url = 'https://f1113.wonderfulday30.live/search.php'
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

    def get_pic_list(self, detail_url):
        title = ''
        driver = webdriver.Chrome(options=self.options)
        try:
            driver.get(detail_url)
            # driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, self.long_wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='threadtitle']/h1")))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath("//div[@id='threadtitle']/h1/text()")[0]
            block = selector.xpath('//div[@id="threadtitle"]/../div[@class="locked"]')
            content_list = selector.xpath('//div[@id="threadtitle"]/../div[2]//text()')
            author = selector.xpath('//div[@id="postlist"]/div[1]//div[@class="postinfo"]/a/text()')[0]
            str_content = ''.join(content_list).replace(" ", '').replace("\n", '')
            if block:
                return [], '禁言-' + title
            if ('删' in title):
                return [], '标题删除-' + title
            if (len(str_content) < 100) and ('删' in str_content):
                return [], '正文删除-' + title
            if len(str_content) < 200:
                return [], '内容太短-' + title
            if author == 'admin':
                return [], '管理员贴-' + title

            wait = WebDriverWait(driver, self.long_wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, "//img[starts-with(@file,'http')]")))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            pic_url_list = selector.xpath("//img[starts-with(@file,'http')]/@file")
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            if not pic_url_list:
                title = '空列表-' + title
            return pic_url_list, title, author
        except Exception as e:
            print('get_pic_list失败:{}\nException:{}'.format(detail_url, repr(e)))
            return [], '失败-' + title, ''
        finally:
            driver.quit()

    def check_repeat_url(self, url):
        try:
            query = urlsplit(url).query
            params = parse_qs(query)
            unique_str = params.get('tid')[0]
            if unique_str in self.content:
                self.repeat_num += 1
                print('repeat_num:%s' % self.repeat_num)
                print('已经下载过：%s' % (url))
                return True
        except Exception:
            print(traceback.format_exc())

    def search_action(self, text, type):
        self.login()
        self.driver.get(self.search_url)
        search_button = self.driver.find_element_by_xpath('//button[@id="searchsubmit"]')
        try:
            if type == 'title':
                title_input = self.driver.find_element_by_xpath('//input[@id="srchtxt"]')
                title_input.send_keys(text)
            if type == 'author':
                advanced_button = self.driver.find_element_by_xpath('//p[@class="searchkey"]/a')
                advanced_button.click()
                author_input = self.driver.find_element_by_xpath('//input[@id="srchname"]')
                author_input.send_keys(text)
            search_button.click()
            self.page_url = self.driver.current_url
        except Exception as e:
            raise e

    def get_search_url_list(self):
        try:
            self.driver.get(self.page_url)
            wait = WebDriverWait(self.driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//th[@class="subject"]/a')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            url_list = selector.xpath('//th[@class="subject"]/a/@href')
        except Exception as e:
            return []
        return url_list

    def login(self):
        try:
            self.driver.get(self.home_url)
            login_btn = self.driver.find_element_by_xpath('//div[@id="umenu"]/a[position()=2]')
            login_btn.click()
            wait = WebDriverWait(self.driver, self.wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="username"]')))
            username_input = self.driver.find_element_by_xpath('//input[@name="username"]')
            password_input = self.driver.find_element_by_xpath('//input[@name="password"]')
            enter = self.driver.find_element_by_xpath('//button[@name="loginsubmit"]')
            # username_input.send_keys(nineporn_username)
            # password_input.send_keys(nineporn_password)
            enter.click()
        except Exception as e:
            raise e

    def download_search(self, text, type):
        self.search_action(text, type)
        while True:
            url_list = self.get_search_url_list()
            url_list = [urljoin(self.pre_url, url) for url in url_list]
            self.single_thread_download(url_list)
            next_page = self.get_next_page()
            if not next_page:
                print('最后一页:%s' % self.page_url)
                self.driver.quit()
                break

    def get_user_list(self):
        try:
            self.driver.get(self.page_url)
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(self.driver, self.wait_time)
            user_list_xpath = '//tbody//td[@class="author"]//a/text()'
            wait_xpath = user_list_xpath.rsplit('/', maxsplit=1)[0]
            wait.until(EC.presence_of_element_located((By.XPATH, wait_xpath)))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            user_list = selector.xpath('//tbody//td[@class="author"]//a/text()')
        except Exception as e:
            print('get_user_list失败:{}\nException:{}'.format(self.page_url, repr(e)))
            return []
        print('%s:get_user_list获取完成:%s' % (len(user_list), self.page_url))
        return user_list

    def get_big_user(self):
        all_user_set = set()
        while True:
            user_list = self.get_user_list()
            all_user_set |= set(user_list)
            next_page = self.get_next_page()
            if not next_page:
                print('最后一页:%s' % self.page_url)
                self.driver.quit()
                break

        try:
            with open('../file/big_user.txt', 'r', encoding='utf8') as f:
                user_list = f.readlines()
                user_list = [user.strip() for user in user_list]
            all_user_set |= set(user_list)
        except FileNotFoundError:
            pass
        with open('../file/big_user.txt', 'w', encoding='utf8') as f:
            for user in all_user_set:
                f.write(user + "\n")


if __name__ == '__main__':
    # gem = NinePorn('gem', mutil_thread=True)
    # gem.main()
    # all = NinePorn('all', mutil_thread=True)
    # all.main()
    ori = NinePorn('ori_gem')
    ori.main()
    # ori.get_big_user()

    # np = NinePorn()
    # np.download_search(text='lvcha7777', type='author')
    # np.download_search(text='露脸', type='title')
