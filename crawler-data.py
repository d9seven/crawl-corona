import requests
import dryscrape
import time
import operator
import re
from bs4 import BeautifulSoup
from environs import Env
from requests_html import HTMLSession
from selenium import webdriver

env = Env()
env.read_env()

CORONA_ANALYTICS_URL = env('CORONA_ANALYTICS_URL')
CORONA_HOME_URL = env('CORONA_HOME_URL')
USER_ACCESS_TOKEN = env('USER_ACCESS_TOKEN')
GRAPH_URL = env('GRAPH_URL')
PAGE_ID = env('PAGE_ID')
USER_ID = env('USER_ID')
APP_ID = env('APP_ID')
APP_SECRET = env('APP_SECRET')
GRAP_API_VER = env('GRAP_API_VER')
TOOL_ACCESSTOKEN_URL = env('TOOL_ACCESSTOKEN_URL')

class Main(object):
  def __init__(self, url, page_id, user_token, app_id, app_secret):
    self.url = url
    self.page_id = page_id
    self.user_token = user_token
    self.app_id = app_id
    self.app_secret = app_secret
    
  def set_driver(self):
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    driver = webdriver.Chrome('./chromedriver', options=option)
    return driver
  
  def visit_tool_access_token(self):
    print('Waiting to visit Tool Access Token page...!')
    driver = self.set_driver()
    driver.get(TOOL_ACCESSTOKEN_URL)
    time.sleep(2)
    print("Ok!")
    return driver
  
  def visit_analytics_page(self):
    print('Waiting to visit Analytics page...!')
    driver = self.set_driver()
    driver.get(CORONA_ANALYTICS_URL)
    time.sleep(2)
    print("Ok!")
    return driver
  
  def visit_home_page(self):
    print('Waiting to visit Home page...!')
    driver = self.set_driver()
    driver.get(CORONA_HOME_URL)
    time.sleep(2)
    print("Ok!")
    return driver
  
  def get_rate(self, driver):
    percent_data = []
    percents = driver.find_elements_by_class_name('nested-number')
    for i in percents:
      get_class = i.find_element_by_tag_name('i').get_attribute('class')
      if get_class == 'fa fa-arrow-up':
        get_class = "Tăng"
      else:
        get_class = "NA"
      percent_data.append(get_class)

    rate = driver.find_elements_by_class_name('text-recovered')
    rate_nhiem = f'{percent_data[0]} {rate[0].text}'
    rate_tu_vong = f'{percent_data[1]} {rate[1].text}'
    rate_binh_phuc = f'{percent_data[2]} {rate[2].text}'
    return [rate_nhiem, rate_tu_vong, rate_binh_phuc]
  
  def get_top_vn(self, drive):
    data = []
    get_list_group = drive.find_elements_by_class_name('list-group')[0]
    get_item = get_list_group.find_elements_by_class_name('list-group-item')
    get3vn = operator.itemgetter(0, 1, 2)
    top3_vn = get3vn(get_item)
    for i in top3_vn:
      get_span = i.find_elements_by_tag_name('span')
      tinh_thanh = get_span[0].text
      nhiem_benh = get_span[1].text
      binh_phuc = '0'
      tu_vong = '0'
      if len(get_span) == 3:
        binh_phuc = get_span[2].text
      if len(get_span) == 4:
        tu_vong = get_span[3].text
      data.append(f'{tinh_thanh} | Nhiễm bệnh ({nhiem_benh}) | Bình phục ({binh_phuc}) | Tử Vong ({tu_vong})')
    return data
  
  def get_top_qt(self, drive):
    data = []
    get_list_qt = drive.find_elements_by_class_name('list-group')[1]
    get_item_qt = get_list_qt.find_elements_by_class_name('list-group-item')
    get3qt = operator.itemgetter(0, 1, 2)
    top3_qt = get3qt(get_item_qt)
    for i in top3_qt:
      get_span = i.find_elements_by_tag_name('span')
      tinh_thanh = i.text.split('\n')[0]
      nhiem_benh = get_span[0].text
      binh_phuc = get_span[1].text
      tu_vong = get_span[2].text
      data.append(f'{tinh_thanh} | Nhiễm bệnh ({nhiem_benh}) | Bình phục ({binh_phuc}) | Tử Vong ({tu_vong})')
    return data
    
  def get_home_data(self):
    home_data = self.visit_home_page()
    analytics_data = self.get_analytics_data()
    
    get_first_line = home_data.find_elements_by_class_name('first-line')
    so_nguoi_nhiem = get_first_line[0].text
    so_nguoi_tu_vong = get_first_line[1].text
    so_nguoi_binh_phuc = get_first_line[2].text
    
    rate = self.get_rate(home_data)
    rate_nhiem = rate[0]
    rate_tu_vong = rate[1]
    rate_binh_phuc = rate[2]
    
    viet_nam_data = home_data.find_element_by_class_name('confirmed-box')
    find_div = viet_nam_data.find_elements_by_tag_name('div')
    tong_ca_nhiem_vn = find_div[0].text.split('\n')[1].strip()
    nhiem_benh_vn = find_div[1].text.split('\n')[0].strip()
    binh_phuc_vn = find_div[1].text.split('\n')[1].strip()
    
    top_trong_nuoc = self.get_top_vn(home_data)
    top_quoc_te = self.get_top_qt(home_data)
    message = f'[BOT] Tự động cập nhật tình hình dịch bệnh COVID-19 @[{USER_ID}]\n\n' \
            f'{self.show_time_update(home_data)}\n\n' \
            f'Việt Nam:\n' \
            f'- {tong_ca_nhiem_vn}\n' \
            f'- {nhiem_benh_vn}\n' \
            f'- {binh_phuc_vn}\n\n' \
            f'Top 3 tỉnh thành trong nước nhiễm bệnh nhiều nhất:\n' \
            f'- {top_trong_nuoc[0]}\n' \
            f'- {top_trong_nuoc[1]}\n' \
            f'- {top_trong_nuoc[2]}\n\n' \
            f'Toàn Thế Giới:\n' \
            f'- Số người nhiễm: {so_nguoi_nhiem} | {rate_nhiem}\n' \
            f'- Số người tử vong: {so_nguoi_tu_vong} | {rate_tu_vong}\n' \
            f'- Số người bình phục: {so_nguoi_binh_phuc} | {rate_binh_phuc}\n' \
            f'- SỐ NGƯỜI ĐANG BỊ NHIỄM BỆNH: {analytics_data[0]}\n\n' \
            f'Top 3 Quốc gia nhiễm bệnh nhiều nhất:\n' \
            f'- {top_quoc_te[0]}\n' \
            f'- {top_quoc_te[1]}\n' \
            f'- {top_quoc_te[2]}\n' \

    print(message)
    return message
  
  def show_time_update(self, driver):
    time_update = driver.find_element_by_class_name('title-widget')
    time = time_update.text
    src = 'Nguồn: WHO, CDC, NHC, DXY, Bộ Y Tế Việt Nam.'
    return f'{time}\n{src}'
  
  def get_analytics_data(self):
    data_vietnam = None
    analytics_data = self.visit_analytics_page()
    data = analytics_data.find_elements_by_tag_name('h2')
    vietnam_data = analytics_data.find_elements_by_class_name('public_fixedDataTable_bodyRow')
    for i in vietnam_data:
      get_data_vn = i.text.split('\n')[0]
      if get_data_vn == 'Vietnam':
        data_vietnam = i
    so_nguoi_tu_vong_vn = data_vietnam.text.split('\n')
    dang_nhiem = data[3].text
    return [dang_nhiem, so_nguoi_tu_vong_vn]
  
  def expires_in_token(self):
    driver = self.visit_tool_access_token()
    debug_token_url = f'https://developers.facebook.com/tools/debug/accesstoken/?access_token={USER_ACCESS_TOKEN}&version=v6.0'
    res = requests.get(debug_token_url)
    token = None
    return token
  
  def page_publish_post(self, message):
    user_token = USER_ACCESS_TOKEN
    get_page_token = f"{GRAPH_URL}/{self.page_id}?fields=access_token&access_token={user_token}"
    data = requests.get(get_page_token)
    page_token = data.json()['access_token']
    
    url_posts = f"{GRAPH_URL}/{self.page_id}/feed?message={message}&access_token={page_token}"
    res = requests.post(url_posts)
    post_id = res.json()['id']
    self.comment_page_post(post_id, page_token)
    print('Publish Done!')
    
  def comment_page_post(self, post_id, page_token):
    message = f"[BOT] Bot đươc tạo bởi Admin (Phạm Đức) @[{USER_ID}]"
    url = f"https://graph.facebook.com/{post_id}/comments?" \
          f"access_token={page_token}&" \
          f"message={message}"
    requests.post(url)
    print('Comment Done!')
    
if __name__ == '__main__':
  main = Main(CORONA_ANALYTICS_URL, PAGE_ID, USER_ACCESS_TOKEN, APP_ID, APP_SECRET)
  message = main.get_home_data()
  main.page_publish_post(message)
  # main.expires_in_token()
