import base64
import json
import os
import random
import re
import time
from urllib import parse

import requests


class XYW:
    def __init__(self, workspace):
        # 请求头
        self.headers = {
            'Host': 'xyw.hainanu.edu.cn',
            'Connection': 'keep-alive',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://xyw.hainanu.edu.cn/srun_portal_pc?ac_id=1&theme=pro',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cookie': 'lang=zh-CN'
        }

        # 接口地址
        self.index_url = 'https://xyw.hainanu.edu.cn/srun_portal_pc?ac_id=1&theme=pro'
        self.status_url = 'https://xyw.hainanu.edu.cn/cgi-bin/rad_user_info?'
        self.token_url = 'https://xyw.hainanu.edu.cn/cgi-bin/get_challenge?'
        self.login_url = 'https://xyw.hainanu.edu.cn/cgi-bin/srun_portal?'

        # 指定工作目录，方便集成脚本到其他工具（如 utools）
        os.chdir(workspace)
        self.config = json.load(open('config.json'))

        # 初始化时间戳
        self.cb_time = int(time.time() * 1000)

        # 随机callback名称
        suffix = str(random.random())
        while len(suffix) != 18:
            suffix = str(random.random())
        jQuery_cb = 'jQuery1124' + re.sub(r'\D', '', suffix)
        self.callback_str = jQuery_cb + '_' + str(self.cb_time)

    # 合并请求，最终登录
    def run(self):
        self.get_ip()
        self.get_token()
        self.calc_argus()
        self.login()

    # 查询登录状态
    def query_status(self):
        # status 请求参数
        status_params = {
            'callback': self.callback_str,
            '_': self.cb_time + 1
        }
        # 查询状态
        status_res = requests.get(self.status_url + parse.urlencode(status_params), headers=self.headers)
        print(status_params)
        print(status_res.text)

    # 获取 ip 并更新配置
    def get_ip(self):
        ip = re.search(r'ip\s*: "(.*?)",', requests.get(self.index_url).text).group(1)
        self.config.update({'ip': ip})

    # 获取 token 并更新配置
    def get_token(self):
        # token请求参数
        token_params = {
            'callback': self.callback_str,
            'username': self.config['username'],
            'ip': self.config['ip'],
            '_': self.cb_time + 2
        }

        token_res = requests.get(self.token_url + parse.urlencode(token_params), headers=self.headers)
        token = re.search(r'"challenge":"(.*?)",', token_res.text).group(1)
        self.config.update({'token': token})

    # 计算请求参数
    def calc_argus(self):
        # 切换至js文件目录
        os.chdir(os.path.join(os.getcwd(), 'js'))

        # 计算 hmd5 和 info 并更新
        config_str1 = base64.b64encode(json.dumps(self.config).encode()).decode()
        self.config.update({
            'hmd5': os.popen(f'node pwd.js {config_str1}').read().strip(),
            "i": os.popen(f'node info.js {config_str1}').read().strip()
        })

        # 计算 checksum 并更新
        config_str2 = base64.b64encode(json.dumps(self.config).encode()).decode()
        self.config.update({'checksum': os.popen(f'node checksum.js {config_str2}').read().strip()})

    # 登录
    def login(self):
        # 登录请求参数
        login_params = {
            'callback': self.callback_str,
            'action': 'login',
            'username': self.config['username'],
            'password': '{MD5}' + self.config['hmd5'],
            'os': self.config['os'],
            'name': self.config['name'],
            'double_stack': self.config['double_stack'],
            'chksum': self.config['checksum'],
            'info': self.config['i'],
            'ac_id': self.config['acid'],
            'ip': self.config['ip'],
            'n': self.config['n'],
            'type': self.config['type'],
            '_': self.cb_time + 3
        }

        final_url = self.login_url + parse.urlencode(login_params)
        requests.get(final_url, headers=self.headers)


if __name__ == '__main__':
    login = XYW(r'D:\TASK\Program\Python\project\demo\src\xywlogin')
    login.run()