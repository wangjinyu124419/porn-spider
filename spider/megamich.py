from nineporn import *
from utils.baidu_translate import baidu_tranlate
def count_time(fun):
    @wraps(fun)
    def warpper(*args):
        s_time = time.time()
        res = fun(*args)
        e_time = time.time()
        t_time = e_time - s_time
        print('%s耗时：%s' % (fun.__name__, t_time))
        return res
    return warpper

class Megamich(NinePorn):

    def __init__(self,type=None):
        super(Megamich, self).__init__()
        # chrome_options.add_argument("--window-size=0,0")
        self.pre_url = 'http://megamich.com'
        self.finish_file = '../file/Megamich.txt'
        self.page_url = 'http://megamich.com/jd/'
        self.root_dir = r'K:\爬虫\megamich'

    @count_time
    def get_url_list(self):
        try:
            self.driver.get(self.page_url)
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(self.driver, 30)
            wait.until(EC.presence_of_element_located((By.XPATH, '//ul[@class="list-normal"]/article//h2/a')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            url_list = selector.xpath('//ul[@class="list-normal"]/article//h2/a/@href')
            fix_url_list = [ url if url.startswith('http') else self.pre_url+url  for url in url_list]
        except Exception:
            print(traceback.format_exc())
            print(self.page_url)
            return []
        print('%s:url_list获取完成:%s'%(len(url_list),self.page_url))
        return fix_url_list

    # @count_time
    def get_pic_list(self, detail_url):
        title = ''
        # self.chrome_options.add_argument('headless')
        # driver = webdriver.Chrome(chrome_options=self.chrome_options)

        try:
            # driver.maximize_window()
            self.driver.minimize_window()
            self.driver.get(detail_url)
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(self.driver, self.title_time)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div/h1")))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath("//div/h1/text()")[0]
            wait = WebDriverWait(self.driver, self.pic_list_time)
            # wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="entry_content"]/li//img')))
            wait.until(EC.presence_of_element_located((By.XPATH, '//img[starts-with(@src,"/wp-content/uploads/img")]')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            # pic_url_list = selector.xpath('//div[@id="entry_content"]/li//img/@src')
            pic_url_list = selector.xpath('//img[starts-with(@src,"/wp-content/uploads/img")]/@src')
            fix_pic_url_list = [ pic_url if pic_url.startswith('http') else self.pre_url+pic_url  for pic_url in pic_url_list]
            print("fix_pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            # pic_url_list=[self.pre_url+pic_url for pic_url in pic_url_list]
            # pic_url_list=[self.pre_url+pic_url for pic_url in pic_url_list]
            return fix_pic_url_list, title
        except Exception:
            print('get_pic_list失败：%s'%detail_url)
            # print(traceback.format_exc())
            return [],'失败-' + title
        # finally:
        #     driver.close()


    @count_time
    def download(self, detail_url):
        pic_list, title = self.get_pic_list(detail_url)
        tranlate_title = baidu_tranlate(title)
        if tranlate_title:
            title = tranlate_title +'_____'+title
        if len(pic_list) < 10:
            print('图片过少:%s' % detail_url)
            return
        if not pic_list:
            print('pic_list为空-%s:%s'%(title,detail_url))
            self.record_finish_url(detail_url,title)
            return
        print('开始下载:%s' % detail_url)

        # legal_title = re.sub(r"[\/\\\:\*\?\"\<\>\|!！\.\s]", "", title)
        legal_title = re.sub(r"[^\w]", "", title)
        path = os.path.join(self.root_dir, legal_title)

        if not os.path.exists(path):
            os.makedirs(path)
        g_list = []
        for pic_url in pic_list:
            g_list.append(gevent.spawn(self.save_pic, pic_url, legal_title))
        gevent.joinall(g_list)
        return legal_title

    @count_time
    def get_next_page(self):
        for i in range(3):
            try:
                self.driver.get(self.page_url)
                wait = WebDriverWait(self.driver, self.next_page_time*(i+1))
                wait.until(EC.presence_of_element_located((By.XPATH, '//a[@class="next page-numbers"]')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                # next_page = selector.xpath('//a[@class="next page-numbers"]/text()')
                # print('next_page:%s' % next_page[0])
                next_url = selector.xpath('//a[@class="next page-numbers"]/@href')[0]
                print('next_url:%s' % next_url)
                self.page_url = next_url
                return True
            except Exception as e:
                print(e,self.page_url)
                print(traceback.format_exc())
                time.sleep(i*10)
                continue
        return False

if __name__ == '__main__':
    mg = Megamich()
    mg.main()
