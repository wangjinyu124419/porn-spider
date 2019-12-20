import requests
import selenium
from lxml import etree
from selenium import webdriver
import re

def get_twitter(file):
    with open(file,encoding='utf8') as f:
        files = f.readlines()
        for file in files:
            res=re.match('.*(pic.twitter.com.*)',file)
            if res:
                print(res.group(1))



# detail_url='https://twitter.com/gagaflashing/status/1207641110698291200'
# log_url='https://twitter.com/login'
# driver = webdriver.Chrome()
# driver.get(log_url)
# username = driver.find_element_by_xpath('//div[@class="page-canvas"]//input[@name="session[username_or_email]"]')
# password = driver.find_element_by_xpath('//div[@class="page-canvas"]//input[@name="session[password]"]')
# enter = driver.find_element_by_xpath('//button[@type="submit"]')
# username.send_keys('Jordan124419')
# password.send_keys('1244192592wang')
# enter.click()
# driver.get(detail_url)
# import time
# time.sleep(10)
# page_source = driver.page_source
# print(page_source)
# selector = etree.HTML(page_source)
# url_list = selector.xpath('//div[@aria-label="图像"]/img/@src')
# print(url_list)
if __name__ == '__main__':
    get_twitter('file.txt')


