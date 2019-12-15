from nineporn import *
from config import USERNAME,PASSWORD


class SexBar(NinePorn):
    proxies = {
        'http': 'http://127.0.0.1:1080',
        'https': 'https://127.0.0.1:1080',
    }
    root_dir = r'K:\爬虫\sexbar'
    finish_file = 'sexbar.txt'
    login_url = 'http://sex8.cc/portal.html'
    page_url = 'http://sex8.cc/forum-111-1.html'
    pre_url = 'http://sex8.cc/'
    def __init__(self,username=None,password=None):
        if not username:
            self.username=USERNAME
        if not password:
            self.password=PASSWORD

    @count_time
    def login(self):
        for i in range(5):
            try:
                driver.get(self.login_url)
                wait = WebDriverWait(driver, 60)
                wait.until(EC.presence_of_element_located((By.ID, 'login_btn')))
                driver.maximize_window()
                ad_btn = driver.find_element_by_xpath("//a[@class='close_index']")
                if ad_btn:
                    ad_btn.click()
                login_btn = driver.find_element_by_xpath("//div[@id='login_btn']")
                login_btn.click()
                wait.until(EC.presence_of_element_located((By.NAME, 'username')))
                username = driver.find_element_by_xpath("//input[@name='username']")
                password = driver.find_element_by_xpath("//input[@name='password']")
                enter = driver.find_element_by_xpath("//button[@name='loginsubmit']")
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
            driver.get(self.page_url)
            wait = WebDriverWait(driver, 60)
            wait.until(EC.presence_of_element_located((By.XPATH, '//tbody[starts-with(@id,"normalthread")]/tr[2]//a')))
            page_source = driver.page_source
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
            driver.get(detail_url)
            wait = WebDriverWait(driver, 120)
            wait.until(EC.presence_of_element_located((By.XPATH, '//span[@id="thread_subject"]')))
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')

            wait = WebDriverWait(driver, 180)
            wait.until(EC.presence_of_element_located((By.XPATH, '//img[starts-with(@id,"aimg")]')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath("//span[@id='thread_subject']/text()")[0]
            # pic_url_list = selector.xpath('//img[starts-with(@id,"aimg")]/@file')
            pic_url_list = selector.xpath('//ignore_js_op//img/@file')

            if not pic_url_list:
                # pic_url_list = selector.xpath('//img[starts-with(@id,"aimg")]/@src')
                pic_url_list = selector.xpath('//ignore_js_op//img/@src')

            if not pic_url_list:
                # pic_url_list = selector.xpath('//img[starts-with(@id,"aimg")]/@src')
                pic_url_list = selector.xpath('//td[starts-with(@id,"postmessage")]//img[starts-with(@id,"aimg")]/@src')
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            if not pic_url_list:
                title= '空列表-' + title
            return pic_url_list, title
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return [], '失败-' + title


    def get_next_page(self):
        for i in range(5):
            try:
                driver.get(self.page_url)
                wait = WebDriverWait(driver, 60)
                wait.until(EC.presence_of_element_located((By.XPATH, '//a[text()="下一页"]')))
                page_source = driver.page_source
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
    # caoliu.download('https://www.t66y.com/htm_data/1907/16/3597142.html')
