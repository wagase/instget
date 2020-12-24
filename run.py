#! python 
# -*- coding: utf-8 -*-

import os
import re
import json
import requests
import urllib.request
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.action_chains  import ActionChains
from selenium.webdriver.common.keys import Keys

class InstaImgCollector:

    def __init__(self):
        self.fast_mode = False # 1ページだけ実行するならTrue。全取得ならFalse
        self.img_code_list = []
        self.img_url_list = []
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--no-sandbox')
        # chromedriverの場所設定
        self.driver = webdriver.Chrome(executable_path='D:\chromedriver_win32\chromedriver.exe', options=self.options)
        self.action = ActionChains(self.driver)
        # 自分のインスタIDとパスワード
        self.USER = "xxxxxxx"
        self.PASS = "xxxxxxxxxxxxx"

    def mid(self,text,s,e):
        return text[s-1:s+e-1]

    def left(self,text,e):
        return text[:e]

    def right(self,text,s):
        return text[-s:]

    def return_img_pattern(self):
        html_source = self.driver.page_source
        pattern = 'https:\/\/scontent-.*?\.jpg.*?","config_width"'
        results = re.findall(pattern, html_source, re.S)
        return results

    def return_video_pattern(self):
        html_source = self.driver.page_source
        pattern = 'video_url":"https://scontent.*\.mp4.*?"'
        results = re.findall(pattern, html_source, re.S)
        return results

    def return_code_pattern(self):
        html_source = self.driver.page_source
        pattern = '><a href="/p/(.*?)/"'
        results = re.findall(pattern, html_source, re.S)
        return results

    def login(self):
        url = "https://www.instagram.com/"
        self.driver.get(url)
        sleep(3)
        usernamebox = self.driver.find_element_by_name("username")
        usernamebox.send_keys(self.USER)
        passwordbox = self.driver.find_element_by_name("password")
        passwordbox.send_keys(self.PASS)
        sleep(1)
        self.driver.find_element_by_xpath("//button[@type='submit']").click()
        sleep(3)

    def fetch_img_url(self, target_code):
        url = "https://www.instagram.com/p/{}".format(target_code)
        self.driver.get(url)
        url_list = self.return_img_pattern()
        for strjpg in url_list:
            if (len(strjpg)<330):
                strjpg = strjpg.replace("\\u0026","&")
                strjpg = self.left(strjpg,len(strjpg)-16)
                if ("/e35/" in strjpg) & ("640x640" not in strjpg) & ("750x750" not in strjpg):
                    if strjpg not in self.img_url_list:
                        new_url = strjpg
                        self.img_url_list.append(new_url)
        url_list = self.return_video_pattern()
        for strmp4 in url_list:
            if (len(strmp4)<330):
                strmp4 = self.right(strmp4,len(strmp4)-12)
                strmp4 = self.left(strmp4,len(strmp4)-1)
                strmp4 = strmp4.replace("\\u0026","&")
                if strmp4 not in self.img_url_list:
                    new_url = strmp4
                    self.img_url_list.append(new_url)
        return self.img_url_list

    def fetch_code_url(self, target_username):
        url = "https://www.instagram.com/{}".format(target_username)
        self.driver.get(url)
        self.driver.maximize_window()
        # 過去にやったcodeを取得
        log_list = self.read_code_log()
        if self.fast_mode:
            sleep(1)
            code_list = self.return_code_pattern()
            for code_id in code_list:
                if code_id not in self.img_code_list:
                    # 過去にやったcodeは除外する
                    if code_id + '\n' in log_list:
                        continue
                    self.img_code_list.append(code_id)
                    self.write_code_log(code_id)
        else:
            for i in range(60):
                sleep(1)
                # i x 10000px スクロール
                self.driver.execute_script('window.scrollTo(0, '+ str(i) +'0000);')
                sleep(1)
                code_list = self.return_code_pattern()
                for code_id in code_list:
                    if code_id not in self.img_code_list:
                        # 過去にやったcodeは除外する
                        if code_id + '\n' in log_list:
                            continue
                        self.img_code_list.append(code_id)
                        self.write_code_log(code_id)

        return self.img_code_list

    def download_img(self, url, save_file_path):
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            urllib.request.urlretrieve(url, save_file_path)

    def get_post_url_from_id(self, id_):
        self.img_url_list = self.fetch_img_url(target_code=id_)

    def get_code_id_from_id(self, id_):
        # codeIDの一覧を取得
        self.img_code_list = self.fetch_code_url(target_username=id_)
        for code_id in self.img_code_list:
            self.get_post_url_from_id(code_id)
        return self.img_url_list

    def quit(self):
        self.driver.quit()

    def clear(self):
        self.img_code_list = []
        self.img_url_list = []

    def write_code_log(self, txt):
        path = 'log/getcode.log'
        with open(path, mode='a') as f:
            f.write(txt+'\n')

    def read_code_log(self):
        path = 'log/getcode.log'
        with open(path) as f:
            l = f.readlines()
        return l


if __name__ == '__main__':
    # 取得したい人のインスタIDのリスト
    inst_list = ['aaaaa','bbbbb','ddddd','eeeee','cccccc']
    iic = InstaImgCollector()
    iic.login()
    for inst_id in inst_list:
        # フォルダ作成
        os.makedirs('data/' + inst_id ,exist_ok=True)
        url_list = iic.get_code_id_from_id(inst_id)
        iic.clear()
        for url_i in url_list:
            m = re.search(r'/([0-9]+.*jpg)',url_i)
            if m:
                file_name = 'data/' + inst_id + m.group()
                iic.download_img(url_i, file_name)
            m = re.search(r'/([0-9]+.*mp4)',url_i)
            if m:
                file_name = 'data/' + inst_id + m.group()
                iic.download_img(url_i, file_name)
    iic.quit()
