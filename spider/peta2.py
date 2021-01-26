from spider.base import *


class Peta(BasePorn):
    def __init__(self,
                 page_url='https://5689.peta2.jp/1900985.html',
                 root_dir=r'E:\爬虫\peta2',
                 finish_file_name='peta2.txt',
                 max_repeat_num=100,
                 wait_time=30,
                 long_wait_time=60,
                 disable_load_img=True,
                 headless=True,
                 proxies=None,
                 save_dir=os.path.join(base_dir, 'file'),
                 mutil_thread=True,
                 url_list_xpath='//ul[@class="list-normal"]/li//h3/a/@href',
                 next_page_xpath='//ul[@class="pagination"]/li[last()-1]/a/@href',
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
        self.home_url = 'https://5689.peta2.jp/'

    # @count_time
    def get_pic_list(self, detail_url):
        save_title = ''
        try:
            self.driver.get(detail_url)
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(self.driver, self.long_wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//img[@class="picture"]')))
            page_source = self.driver.page_source
            selector = etree.HTML(page_source)
            pic_url_list = selector.xpath('//ul[@class="list-unstyled"]//img[@class="picture"]/@src')
            save_title = selector.xpath('//div[@class="post-heading"]/h2//text()')
            save_title = ''.join(save_title)
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            return True, pic_url_list, save_title
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return False, [], save_title

    def main(self):
        for url in ['https://5689.peta2.jp/1900988.html',
                    'https://5689.peta2.jp/534680.html',
                    'https://5689.peta2.jp/499765.html',
                    'https://5689.peta2.jp/1911897.html',
                    'https://5689.peta2.jp/1901290.html',
                    'https://5689.peta2.jp/1900985.html',

                    ]:
            self.page_url = url
            while True:
                try:
                    self.download(self.page_url)
                except Exception:
                    print(traceback.format_exc())
                    print('download fail:%s' % self.page_url)
                next_page = self.get_next_page()
                if not next_page:
                    print('最后一页:%s' % self.page_url)
                    self.driver.close()
                    break


if __name__ == '__main__':
    peta = Peta()
    peta.main()
