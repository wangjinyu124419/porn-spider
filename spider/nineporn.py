from urllib.parse import urlsplit, parse_qs
from xml.etree.ElementTree import tostring

from selenium.common.exceptions import TimeoutException

from config import nineporn_username, nineporn_password
from spider.base import *


class NinePorn(BasePorn):
    type_dict = {
        'gem': {
            # 'page_url': 'https://f1113.wonderfulday30.live/forumdisplay.php?fid=19&filter=digest',
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
                 category='all',
                 finish_file_name='nineporn.txt',
                 max_repeat_num=1000,
                 wait_time=30,
                 long_wait_time=60,
                 disable_load_img=True,
                 headless=True,
                 proxies=None,
                 save_dir=os.path.join(base_dir, 'file'),
                 mutil_thread=True,
                 url_list_xpath='//span[starts-with(@id,"thread")]/a/@href',
                 next_page_xpath='//a[@class="next"]/@href',
                 cookie_file='nineporn_cookie.txt'
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
            cookie_file=cookie_file
        )

    def get_pic_list(self, detail_url, headless=True):
        title = ''
        author = ''
        if headless:
            self.options.add_argument('headless')
        driver = webdriver.Chrome(options=self.options)
        try:
            driver.get(detail_url)
            page_source = driver.page_source
            # driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, self.long_wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="postlist"]/div[1]')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath("//div[@id='threadtitle']/h1/text()")[0]
            author = selector.xpath('//div[@id="postlist"]/div[1]//div[@class="postinfo"]/a/text()')[0]
            pic_url_list = selector.xpath("//img[starts-with(@file,'http')]/@file")
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            return True, pic_url_list, title, author
        except Exception as e:
            print('get_pic_list失败:{}\nException:{}'.format(detail_url, repr(e)))
            return False, [], title, author
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

    def search_action(self, text, type='author', click_advanced=True):
        for i in range(1, 5):
            try:
                self.driver.get(self.search_url)
                search_button = self.driver.find_element_by_xpath('//button[@id="searchsubmit"]')
                if type == 'title':
                    title_input = self.driver.find_element_by_xpath('//input[@id="srchtxt"]')
                    title_input.send_keys(text)
                if type == 'author':
                    author_input = self.driver.find_element_by_xpath('//input[@id="srchname"]')
                    page_source = self.driver.page_source
                    selector = etree.HTML(page_source)
                    is_show_advanced = selector.xpath('//div[@id="search_option"]/@style')
                    if is_show_advanced:
                        advanced_button = self.driver.find_element_by_xpath('//p[@class="searchkey"]/a')
                        advanced_button.click()
                    author_input.send_keys(text)
                search_button.click()
                wait = WebDriverWait(self.driver, self.wait_time)
                wait.until(EC.presence_of_element_located((By.XPATH, '//form[@class="searchform"]')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                search_result = selector.xpath('//div[@class="searchlist threadlist datalist"]')
                if not search_result:
                    time.sleep(i * 10)
                    continue
                return
            except Exception as e:
                print('搜索异常:{},{}'.format(text, e))
                time.sleep(i * 10)

    def get_search_url_list(self):
        for i in range(3):
            try:
                # self.driver.get(self.page_url)
                wait = WebDriverWait(self.driver, self.wait_time)
                wait.until(
                    EC.presence_of_element_located((By.XPATH, '//div[@id="wrap"]/div/table[@summary="搜索"]/tbody')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                post_list = selector.xpath('//div[@id="wrap"]/div/table[@summary="搜索"]/tbody')
                url_list = []
                for post in post_list:
                    post = tostring(post)
                    selector = etree.HTML(post)
                    url = selector.xpath('//th[@class="subject"]/a/@href')[0]
                    forum = selector.xpath('//td[@class="forum"]/a/text()')[0]
                    if forum == '91自拍达人原创区':
                        continue
                    url_list.append(url)
                return url_list
            except TimeoutException:
                time.sleep((i + 1) * 10)
                continue
            except Exception as e:
                print('get_search_url_list失败:{}\nException:{}'.format(self.page_url, repr(e)))
                return []
        return []

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
            username_input.send_keys(nineporn_username)
            password_input.send_keys(nineporn_password)
            enter.click()
        except Exception as e:
            raise e

    @count_time
    def download(self, detail_url):
        success, pic_list, raw_title, author = self.get_pic_list(detail_url)
        legal_title = re.sub(r"[^\w]", "", raw_title)
        legal_title = convert(legal_title, self.convert_type)
        if not success:
            author_title = '失败-' + '【' + author + '】' + legal_title
        else:
            author_title = '【' + author + '】' + legal_title
        if len(pic_list) < 10:
            print('图片过少:%s' % detail_url)
            return author_title
        old_path = os.path.join(self.root_dir, legal_title)
        new_path = os.path.join(self.root_dir, author_title)
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
        pic_list = [urljoin(self.pre_url, pic_url) for pic_url in pic_list]
        print('开始下载:%s' % detail_url)
        path = os.path.join(self.root_dir, author_title)
        if not os.path.exists(path):
            os.makedirs(path)
        g_list = []
        for pic_url in pic_list:
            g_list.append(gevent.spawn(self.save_pic, pic_url, author_title))
        gevent.joinall(g_list)
        return author_title

    def download_all_search(self):
        big_user_path = os.path.join(self.save_dir, 'big_user.txt')
        with open(big_user_path, 'r', encoding='utf8') as f:
            user_list = [user.strip() for user in f.readlines()]
        self.login()
        for user in user_list[1235:]:
            print('开始下载用户:{}'.format(user))
            self.download_search(user, need_login=False)
            elapsed = self.download_search.elapsed
            # 控制搜索频率
            if elapsed < 10:
                time.sleep(10)
        self.driver.quit()

    @count_time
    def download_search(self, text, search_type='author', need_login=True):
        assert search_type in ['author', 'title'], '搜索类型错误'
        if need_login:
            self.login()
        self.search_action(text, search_type)
        url_list = self.get_search_url_list()
        url_list = [urljoin(self.pre_url, url) for url in url_list]
        self.single_thread_download(url_list)

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
        file_path = os.path.join(self.save_dir, 'big_user.txt')
        try:
            with open(file_path, 'r', encoding='utf8') as f:
                user_list = f.readlines()
                user_list = [user.strip() for user in user_list]
            all_user_set |= set(user_list)
        except FileNotFoundError:
            pass
        with open(file_path, 'w', encoding='utf8') as f:
            for user in all_user_set:
                f.write(user + "\n")

    def rename(self):
        print('开始爬取:{}'.format(self.page_url))
        while True:
            try:
                self.driver.get(self.page_url)
                self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                wait = WebDriverWait(self.driver, self.wait_time)
                wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//table[@summary="forum_19"]/tbody[starts-with(@id,"normalthread")]')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                post_list = selector.xpath('//table[@summary="forum_19"]/tbody[starts-with(@id,"normalthread")]')
                for post in post_list:
                    post = tostring(post)
                    selector = etree.HTML(post)
                    title_list = selector.xpath('//span[starts-with(@id,"thread")]/a/text()')
                    author_list = selector.xpath('//td[@class="author"]/cite//text()')
                    try:
                        title = title_list[-1]
                        author = ''.join(author_list).strip()
                    except Exception:
                        print(title_list, author_list)
                        continue
                    legal_title = re.sub(r"[^\w]", "", title)
                    legal_title = convert(legal_title, self.convert_type)
                    if not legal_title:
                        continue
                    new_title = '【' + author + '】' + legal_title
                    save_path = os.path.join(self.root_dir, legal_title)
                    rename_save_path = os.path.join(self.root_dir, new_title)
                    if os.path.exists(save_path):
                        print(rename_save_path)
                        try:
                            os.rename(save_path, rename_save_path)
                        except Exception as e:
                            print(save_path, rename_save_path)
                            print(e)

            except Exception as e:
                print(e)

            next_page = self.get_next_page()
            if not next_page:
                print('最后一页:%s' % self.page_url)
                self.driver.quit()
                break
        print('结束爬取:{}'.format(self.page_url))


if __name__ == '__main__':
    all = NinePorn('all')
    all.main()
