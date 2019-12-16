from nineporn import *

# 进入浏览器设置
# options = webdriver.ChromeOptions()
# # 设置中文
# options.add_argument('lang=zh_CN.UTF-8')
# # 更换头部
# #User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36
# options.add_argument('user-agent="Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"')
# driver = webdriver.Chrome(chrome_options=options)


class CaoLiu(NinePorn):
    proxies = {
        'http': 'http://127.0.0.1:1080',
        'https': 'https://127.0.0.1:1080',
    }
    root_dir = r'K:\爬虫\1024'
    page_url = 'http://t66y.com/thread0806.php?fid=16&search=&page=1'
    pre_url = 'http://t66y.com/'
    finish_file = 'caoliu..txt'
    def __init__(self):
        pass

    @count_time
    def get_url_list(self):
        try:
            driver.get(self.page_url)
            wait = WebDriverWait(driver, 60)
            wait.until(EC.presence_of_element_located((By.XPATH, '//tbody/tr[position()>11]/td[2]/h3/a')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            url_list = selector.xpath("//tbody/tr[position()>11]/td[2]/h3/a/@href")
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
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, 120)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div[2]/table/tbody/tr/td')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath("//h4/text()")[0]
            # try:
            wait = WebDriverWait(driver, 300)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='tpc_content do_not_catch']")))
            # wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='tpc_content do_not_catch']//img")))
            print('wait1:%s'%detail_url)
            # except Exception:
            #     wait = WebDriverWait(driver, 100)
            #     wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='tpc_content do_not_catch']//input")))
            #     print('wait2:%s'%detail_url)
            # page_source = driver.page_source
            # selector = etree.HTML(page_source)
            pic_url_list = selector.xpath("//div[@class='tpc_content do_not_catch']//@src")
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            if not pic_url_list:
                title = '空列表-' + title
            return pic_url_list, title
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return [], '失败-' + title

    # def save_pic(self, url, path):
    #     name = url.split('/')[-1]
    #     pic_path = os.path.join(self.root_dir, path, name)
    #     if os.path.exists(pic_path):
    #         print('文件已存在:%s' % pic_path)
    #         return
    #     for i in range(5):
    #         try:
    #             status_code = requests.get(url, proxies=self.proxies, timeout=10).status_code
    #             if status_code != 200:
    #                 print("status_code:%s,url:%s" % (status_code,url))
    #                 return
    #             content = requests.get(url, proxies=self.proxies, timeout=20).content
    #             with open(pic_path, 'wb') as f:
    #                 f.write(content)
    #                 print(pic_path)
    #                 break
    #         except Exception as e:
    #             print('save_pic失败第%d次'%(i+1),e)
    #             time.sleep(i)
    #             continue
    #     else:
    #         print(traceback.format_exc())
    #         print('save_pic失败：%s' % url)
    @count_time
    def get_next_page(self):
        for i in range(5):
            try:
                driver.get(self.page_url)
                wait = WebDriverWait(driver, 60)
                wait.until(EC.presence_of_element_located((By.XPATH, '//a[text()="下一頁"]')))
                page_source = driver.page_source
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

    def check_repeat_url(self, url):
        try:
            # unique_key=url.split("/")[-1]
            unique_key=re.match('.*(\d{7}).*', url).group(1)
            with open(self.finish_file, 'r', encoding='utf8') as f:
                content_list = f.readlines()
                for  content in content_list:
                    if unique_key in content:
                        print('已经下载过：%s' % (content.strip()))
                        return True
        except Exception:
            print(traceback.format_exc())

if __name__ == '__main__':
    caoliu = CaoLiu()
    caoliu.main()
    # caoliu.download('https://www.t66y.com/htm_data/1907/16/3597142.html')
