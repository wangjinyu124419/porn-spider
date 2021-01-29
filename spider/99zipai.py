from spider.base import *


class ZiPai(BasePorn):

    def __init__(self,
                 page_url='https://99zipai.com/my/4045/',
                 root_dir=r'E:\爬虫\99zipai\张婉芳',
                 finish_file_name='99zipai.txt',
                 max_repeat_num=1000,
                 first_fetch=False,
                 wait_time=30,
                 long_wait_time=60,
                 disable_load_img=True,
                 headless=True,
                 proxies=None,
                 save_dir=os.path.join(base_dir, 'file'),
                 mutil_thread=True,
                 url_list_xpath='//ul[@class="ul_author_list cl"]/li/a/@href',
                 next_page_xpath='//a[@class="next page-numbers"]/@href',
                 ):
        super().__init__(
            page_url,
            root_dir=root_dir,
            finish_file_name=finish_file_name,
            max_repeat_num=max_repeat_num,
            first_fetch=first_fetch,
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
        # self.options.add_argument('headless')
        driver = webdriver.Chrome(options=self.options)
        try:
            driver.get(detail_url)
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            wait = WebDriverWait(driver, self.long_wait_time)
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="content_left"]/img')))
            page_source = driver.page_source
            selector = etree.HTML(page_source)
            title = selector.xpath('//div[@class="item_title"]/h1/text()')[0]
            pic_url_list = selector.xpath('//div[@class="content_left"]/img/@src')
            print("pic_url_list:%s, url:%s" % (len(pic_url_list), detail_url))
            fix_pic_url_list = [urljoin(self.pre_url, pic_url) for pic_url in pic_url_list]
            return True, fix_pic_url_list, title
        except Exception:
            print('get_pic_list失败：%s' % detail_url)
            print(traceback.format_exc())
            return False, [], title
        finally:
            driver.close()


if __name__ == '__main__':
    zipai = ZiPai(first_fetch=True)
    zipai.main()
