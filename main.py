import json
import requests
import base64
import time
import markdown as md

class backblaze:
    def __init__(self, application_keyid, application_key, bucket_id):
        self.application_key = application_key
        self.application_keyid = application_keyid
        self.bucket_id = bucket_id
        self.auth = None
        self.api_url = None
    
    def get_auth(self):
        # 获取认证信息
        id_and_key = '{}:{}'.format(self.application_keyid, self.application_key)
        basic_auth_string = 'Basic ' + base64.b64encode(bytes(id_and_key, encoding='utf-8')).decode('utf-8')
        headers = { 'Authorization': basic_auth_string }
        r = requests.get('https://api.backblazeb2.com/b2api/v2/b2_authorize_account', headers = headers)
        if r.status_code == 200:
            self.auth = r.json().get('authorizationToken')
            self.api_url = r.json().get('apiUrl')
            return True
        else:
            return False
    
    def get_file_list(self):
        # 获取文件列表
        headers = { 'Authorization': self.auth }
        r = requests.get(self.api_url + '/b2api/v2/b2_list_file_names', headers = headers, params = { 'bucketId': self.bucket_id })
        if r.status_code != 200:
            return []
        res = []
        nowtimestamp = int(time.time() * 1000)
        for per in r.json().get('files'):
            res.append(per.get('fileName'))
            if (nowtimestamp - per.get('uploadTimestamp') > 86400000 * 2):
                break
        return res

def fold(summary, detail):
    return "<details><summary>" + summary + "</summary>" + detail + "</details>\n"

def detailmd(list):
    if (len(list) == 0):
        return "暂无分享的测速数据，不妨在本地测试？\n"
    res = ""
    for per in list:
        summary = "{}: 高速节点 {} 个, 可用节点 {} 个, 时间 {}".format(
            per.get('region'), per.get('good_num'), per.get('running_num'), 
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(per.get('uploadTimestamp') / 1000)))
        detail  = "<p>可用节点订阅：{}<br>".format(per.get('running'))
        detail += "高速节点订阅：{}<br>".format(per.get('good'))
        detail += "低延迟节点订阅：{}</p>".format(per.get('low_delay'))
        res += fold(summary, detail)
        res += "<p></p>"
    return res

def md2html(mdstr):
    exts = ['markdown.extensions.extra', 'markdown.extensions.codehilite','markdown.extensions.tables','markdown.extensions.toc']
    html = '''
    <html>
      <head>
        <title>v2pool 用户分享</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta charset="UTF-8">
        <link rel="stylesheet" type="text/css" href="github.css">
        <script async src="https://cdn.panelbear.com/analytics.js?site=Fr2EL4zRhjK"></script>
        <script>
            window.panelbear = window.panelbear || function() { (window.panelbear.q = window.panelbear.q || []).push(arguments); };
            panelbear('config', { site: 'Fr2EL4zRhjK' });
        </script>
    </head>
    
    <body>
    <div id='content'>
    %s
    </div>
    </body>
    </html>
    '''
    ret = md.markdown(mdstr,extensions=exts)
    return html % ret

if __name__ == '__main__':
    b2 = backblaze('005dd61b9ce80da0000000002', 
        'K005RAPh5+ub6jQ0r32to+qGeU/06GY', 
        '0d7d26114b59ccfe88500d1a')
    if b2.get_auth():
        share = b2.get_file_list()
    else:
        exit()
    
    chinanet = []
    chinamobile = []
    chinaunicom = []
    for per in share:
        url = "https://f005.backblazeb2.com/file/gfwcross-uc/" + per
        r = requests.get(url)
        if r.status_code == 200:
            print("success: " + url)
        else:
            print("failed: " + url)
            continue
        info = json.loads(r.text)
        if info.get('isp') == 'Chinanet':
            chinanet.append(info)
        if info.get('isp') == 'Chinamobile':
            chinamobile.append(info)
        if info.get('isp') == 'Chinaunicom':
            chinaunicom.append(info)
    
    print("Chinanet: " + str(len(chinanet)))
    print("Chinamobile: " + str(len(chinamobile)))
    print("Chinaunicom: " + str(len(chinaunicom)))

    origin_chinanet = len(chinanet)
    origin_chinamobile = len(chinamobile)
    origin_chinaunicom = len(chinaunicom)

    # 如果三者全为空列表，直接结束
    if (len(chinanet) == len(chinamobile) == len(chinaunicom) == 0):
        exit()
    
    # 按照 good_num 排序
    chinanet.sort(key = lambda x: x.get('good_num'), reverse = True)
    chinamobile.sort(key = lambda x: x.get('good_num'), reverse = True)
    chinaunicom.sort(key = lambda x: x.get('good_num'), reverse = True)

    # 如果有空列表，寻找不为空的列表，将其第一个元素放入另外两个列表
    if (len(chinanet) == 0 and len(chinamobile) != 0 and len(chinaunicom) != 0):
        chinanet.append(chinamobile[0])
        chinanet.append(chinaunicom[0])
    if (len(chinamobile) == 0 and len(chinanet) != 0 and len(chinaunicom) != 0):
        chinamobile.append(chinanet[0])
        chinamobile.append(chinaunicom[0])
    if (len(chinaunicom) == 0 and len(chinanet) != 0 and len(chinamobile) != 0):
        chinaunicom.append(chinanet[0])
        chinaunicom.append(chinamobile[0])
    
    # 如果只有一个列表有数据，将其第一个元素放入另外两个列表
    if (len(chinanet) != 0 and len(chinamobile) == 0 and len(chinaunicom) == 0):
        chinamobile.append(chinanet[0])
        chinaunicom.append(chinanet[0])
    if (len(chinanet) == 0 and len(chinamobile) != 0 and len(chinaunicom) == 0):
        chinanet.append(chinamobile[0])
        chinaunicom.append(chinamobile[0])
    if (len(chinanet) == 0 and len(chinamobile) == 0 and len(chinaunicom) != 0):
        chinanet.append(chinaunicom[0])
        chinamobile.append(chinaunicom[0])

    chinanet.sort(key = lambda x: x.get('good_num'), reverse = True)
    chinamobile.sort(key = lambda x: x.get('good_num'), reverse = True)
    chinaunicom.sort(key = lambda x: x.get('good_num'), reverse = True)


    # 下载第一个到文件
    with open('./chinanet.txt', 'w') as f:
        r = requests.get(chinanet[0].get('good'))
        f.write(r.text)
    with open('./chinamobile.txt', 'w') as f:
        r = requests.get(chinamobile[0].get('good'))
        f.write(r.text)
    with open('./chinaunicom.txt', 'w') as f:
        r = requests.get(chinaunicom[0].get('good'))
        f.write(r.text)
    
    # 打印 markdown
    markdown = ""
    markdown += "# v2pool 用户分享\n"
    markdown += "## 项目地址：<https://github.com/gfwcross/v2pool>"
    markdown += "更新时间 {}\n\n".format(time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time())))
    
    markdown += """
**以下为 `base64` 订阅，适用于 `v2rayN`, `Clash for Android` 等客户端。**

- **电信**: `https://nodes.gfwcross.tech/chinanet.txt`

- **移动**: `https://nodes.gfwcross.tech/chinamobile.txt`

- **联通**: `https://nodes.gfwcross.tech/chinaunicom.txt`

"""

    markdown += "\n### 中国电信 Chinanet\n"
    if (origin_chinanet == 0): markdown += "<i>暂无数据, 本数据非电信网络环境测试</i>\n"
    markdown += detailmd(chinanet)
    
    markdown += "\n\n### 中国移动 Chinamobile\n"
    if (origin_chinamobile == 0): markdown += "<i>暂无数据, 本数据非移动网络环境测试</i>\n"
    markdown += detailmd(chinamobile)
    
    markdown += "\n\n### 中国联通 Chinaunicom\n"
    if (origin_chinaunicom == 0): markdown += "<i>暂无数据, 本数据非联通网络环境测试</i>\n"
    markdown += detailmd(chinaunicom) 

    # 输出到 readme.md
    with open('./index.md', 'w', encoding="utf-8") as f:
        f.write(markdown)
    
    # 输出到 readme.html
    with open('./index.html', 'w', encoding="utf-8") as f:
        f.write(md2html(markdown))
