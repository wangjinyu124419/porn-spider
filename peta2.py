from nineporn import *


class Peta(NinePorn):
    def __init__(self):
        super().__init__()
        self.root_dir = r'K:\爬虫\peta2'
        self.page_url = 'https://5689.peta2.jp/1320286_1_ASC.html'
        self.pre_url = 'https://5689.peta2.jp/'
        self.finish_file = 'peta2.txt'
    @count_time
    def get_pic_list(self, detail_url):
        try:
            self.driver.get(detail_url)
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(self.driver, self.pic_list_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//img[@class="picture"]')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            pic_url_list = selector.xpath('//ul[@class="list-unstyled"]//img[@class="picture"]/@src')
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            return pic_url_list
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return []

    @count_time
    def get_next_page(self):
        for i in range(5):
            try:
                self.driver.get(self.page_url)
                wait = WebDriverWait(self.driver, self.next_page_time)
                wait.until(EC.presence_of_element_located((By.XPATH, '//ul[@class="pagination"]/li[last()-1]/a')))
                page_source = self.driver.page_source
                selector = etree.HTML(page_source)
                next_url = selector.xpath('//ul[@class="pagination"]/li[last()-1]/a/@href')[0]
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
            unique_key = re.match('.*(\d{7}).*', url).group(1)
            with open(self.finish_file, 'r', encoding='utf8') as f:
                content_list = f.readlines()
                for content in content_list:
                    if unique_key in content:
                        print('已经下载过：%s' % (content.strip()))
                        return True
        except Exception:
            print(traceback.format_exc())

    @count_time
    def download(self, detail_url):
        pic_list = self.get_pic_list(detail_url)
        if not pic_list:
            print('pic_list为空-%s:%s'%(detail_url))
            return
        print('开始下载:%s' % detail_url)
        g_list = []
        for pic_url in pic_list:
            g_list.append(gevent.spawn(self.save_pic, pic_url))
        gevent.joinall(g_list)

    # @count_time
    def save_pic(self,url):
        try:
            name = re.match('.*(co_.*\.[a-zA-Z]{3})', url).group(1)
        except Exception as e:
            print(e,url)
            return
        pic_path = os.path.join(self.root_dir, name)
        if os.path.exists(pic_path):
            print('文件已存在:%s' % pic_path)
            return
        for i in range(5):
            try:
                status_code = requests.get(url,timeout=10).status_code
                if status_code != 200:
                    print("status_code:%s" % status_code)
                    return
                content = requests.get(url,timeout=20).content
                with open(pic_path, 'wb') as f:
                    f.write(content)
                    print(pic_path)
                    return
            except Exception as e:
                print('保存失败第%d次，url:%s,异常信息:%s'%(i+1,url,e))
                time.sleep(i)
                continue
        else:
            print(traceback.format_exc())
            print('save_pic失败：%s' % url)

    @count_time
    def main(self):
        while True:
            try:
                self.download( self.page_url)
            except Exception:
                print(traceback.format_exc())
                print('download fail:%s' %  self.page_url)
            next_page = self.get_next_page()
            if not next_page:
                print('最后一页:%s'%self.page_url)
                self.driver.close()
                break

if __name__ == '__main__':
    peta = Peta()
    peta.main()
