# 导入必要模块
import requests  # 用于发送网络请求
from bs4 import BeautifulSoup  # 用于解析 HTML 网页
import re  # 用于处理正则表达式
import os  # 用于文件操作
from concurrent.futures import ThreadPoolExecutor, as_completed  # 实现多线程并发

# 定义目标网站列表
urls = [
    'https://api.uouin.com/cloudflare.html',
    'https://ip.164746.xyz',
    'https://cf.vvhan.com/'
]

# 用于匹配 IPv4 的正则表达式
ip_pattern = r'\d{1,3}(?:\.\d{1,3}){3}'

# 判断一个 IP 地址是否有效（格式 + 范围 + 排除特殊 IP）
def is_valid_ip(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        num = int(part)
        if num < 0 or num > 255:
            return False
    if ip in ('0.0.0.0', '127.0.0.1', '255.255.255.255'):
        return False
    return True

# 抓取某个 URL 的 IP 列表，支持多线程
def fetch_ips(url):
    ip_list = []  # 存放当前网址提取到的合法 IP
    try:
        print(f'🔍 正在请求：{url}')
        response = requests.get(url, timeout=10)  # 设置超时时间为10秒
        soup = BeautifulSoup(response.text, 'html.parser')  # 解析 HTML 内容

        # 处理 vvhan 网站，IP 通常在 <textarea class="form-control"> 中
        if url == 'https://cf.vvhan.com/':
            textarea = soup.find('textarea', class_='form-control')
            if textarea:
                lines = textarea.get_text().strip().splitlines()  # 每行可能是一个 IP
                for line in lines:
                    ip_list.extend(re.findall(ip_pattern, line))

        # 处理另外两个网站，IP 在表格的每一行中
        elif url in ('https://api.uouin.com/cloudflare.html', 'https://ip.164746.xyz'):
            elements = soup.find_all('tr')
            for el in elements:
                text = el.get_text().strip()
                ip_list.extend(re.findall(ip_pattern, text))

        # 其他默认处理方式，尝试从 <li> 元素中提取 IP
        else:
            elements = soup.find_all('li')
            for el in elements:
                text = el.get_text().strip()
                ip_list.extend(re.findall(ip_pattern, text))

        # 过滤掉无效 IP
        ip_list = [ip for ip in ip_list if is_valid_ip(ip)]

        print(f'✅ 成功提取 {len(ip_list)} 个 IP 来自：{url}')
        return ip_list

    except requests.exceptions.RequestException as e:
        print(f'⚠️ 请求失败：{url} —— {e}')
    except Exception as e:
        print(f'⚠️ 未知错误：{url} —— {e}')
    return []  # 出错时返回空列表

# 删除旧的 ip.txt 文件
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

# 创建集合用于去重
all_ips = set()

# 使用线程池并发请求所有 URL
with ThreadPoolExecutor(max_workers=5) as executor:
    # 提交所有任务
    future_to_url = {executor.submit(fetch_ips, url): url for url in urls}
    
    # 等待任务完成
    for future in as_completed(future_to_url):
        url = future_to_url[future]
        try:
            ips = future.result()
            all_ips.update(ips)  # 添加到集合（自动去重）
        except Exception as e:
            print(f'❌ 抓取失败（{url}）：{e}')

# 写入 IP 到 ip.txt 文件并打印
try:
    with open('ip.txt', 'w') as file:
        for ip in sorted(all_ips):  # 排序写入
            file.write(ip + '\n')
            print(f'📥 写入 IP：{ip}')
    print(f'🎉 总共提取 {len(all_ips)} 个有效 IP，已保存到 ip.txt。')
except Exception as e:
    print(f'❌ 写入文件失败：{e}')
