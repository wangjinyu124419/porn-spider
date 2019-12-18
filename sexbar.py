from nineporn import *
from config import USERNAME,PASSWORD


class SexBar(NinePorn):
    def __init__(self,username=None,password=None):
        super().__init__()
        self.root_dir = r'K:\爬虫\sexbar'
        self.finish_file = 'sexbar.txt'
        self.login_url = 'http://sex8.cc/portal.html'
        self.page_url = 'http://sex8.cc/forum-111-1.html'
        self.pre_url = 'http://sex8.cc/'
        if not username:
            self.username=USERNAME
        if not password:
            self.password=PASSWORD

    @count_time
    def login(self):
        for i in range(5):
            try:
                self.driver.get(self.login_url)
                wait = WebDriverWait(self.driver, self.login_time)
                wait.until(EC.presence_of_element_located((By.ID, 'login_btn')))
                self.driver.maximize_window()
                ad_btn = self.driver.find_element_by_xpath("//a[@class='close_index']")
                if ad_btn:
                    ad_btn.click()
                login_btn = self.driver.find_element_by_xpath("//div[@id='login_btn']")
                login_btn.click()
                wait.until(EC.presence_of_element_located((By.NAME, 'username')))
                username = self.driver.find_element_by_xpath("//input[@name='username']")
                password = self.driver.find_element_by_xpath("//input[@name='password']")
                enter = self.driver.find_element_by_xpath("//button[@name='loginsubmit']")
                username.send_keys(self.username)
                password.send_keys(self.password)
                enter.click()
                break
            except Exception:
                time.sleep(i*5)
                continue
        print("登录失败")

    @count_time
    def get_url_list(self):
        try:
            self.driver.get(self.page_url)
            wait = WebDriverWait(self.driver, self.url_list_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//tbody[starts-with(@id,"normalthread")]/tr[2]//a')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            url_list = selector.xpath('//tbody[starts-with(@id,"normalthread")]/tr[2]//a/@href')
        except Exception:
            print(traceback.format_exc())
            return []
        print('url_list获取完成:%s' % self.page_url)
        return url_list

    @count_time
    def get_pic_list(self, detail_url):
        title = ''
        try:
            self.driver.get(detail_url)
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(self.driver, self.title_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//span[@id="thread_subject"]')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath("//span[@id='thread_subject']/text()")[0]
            ban = selector.xpath('//div[@id="postlist"]/div[1]//div[@class="locked"]//text()')
            #如果本帖被禁言，则跳过
            if ban:
                print(ban[0])
                return [], '禁言-' + title
            wait = WebDriverWait(self.driver, self.pic_list_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//img[starts-with(@id,"aimg")]')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            pic_url_list = selector.xpath('//ignore_js_op//img/@file')

            if not pic_url_list:
                pic_url_list = selector.xpath('//ignore_js_op//img/@src')

            if not pic_url_list:
                pic_url_list = selector.xpath('//td[starts-with(@id,"postmessage")]//img[starts-with(@id,"aimg")]/@src')
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            if not pic_url_list:
                title= '空列表-' + title
            return pic_url_list, title
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return [], '失败-' + title

    @count_time
    def get_next_page(self):
        for i in range(3):
            try:
                self.driver.get(self.page_url)
                wait = WebDriverWait(self.driver, self.next_page_time)
                wait.until(EC.presence_of_element_located((By.XPATH, '//a[text()="下一页"]')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                next_page = selector.xpath('//a[text()="下一页"]/text()')
                print('next_page:%s' % next_page[0])
                next_url = self.pre_url + selector.xpath('//a[text()="下一页"]/@href')[0]
                print('next_url:%s' % next_url)
                self.page_url = next_url
                return next_url
            except Exception:
                print('获取下一页失败：%s' % self.page_url)
                print(traceback.format_exc())
                continue

    def check_repeat_url(self, url):
        try:
            # unique_key=url.split("/")[-1]
            # unique_key=re.match('.*(\d).*', url).group(1)
            #帖子的ID作为查重key
            unique_key = re.match('.*thread-(\d*).*', url).group(1)
            with open(self.finish_file, 'r', encoding='utf8') as f:
                content_list = f.readlines()
                for  content in content_list:
                    if unique_key in content:
                        print('已经下载过：%s' % (content.strip()))
                        return True
        except Exception:
            print(traceback.format_exc())

if __name__ == '__main__':
    sexbar = SexBar()
    sexbar.main()
    # print(sexbar.get_pic_list('https://sex8.cc/thread-1220722-1-219.html'))
    # caoliu.download('https://www.t66y.com/htm_data/1907/16/3597142.html')
