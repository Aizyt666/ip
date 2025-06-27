# 导入必要模块
import requests  # 用于发送 HTTP 请求
from bs4 import BeautifulSoup  # 用于解析 HTML 页面
import re  # 正则表达式模块，用于提取 IP
import os  # 操作系统模块，用于文件操作
from concurrent.futures import ThreadPoolExecutor, as_completed  # 用于实现多线程

# 定义目标网页列表，这些网页包含 Cloudflare 的 IP 数据
urls = [
    'https://api.uouin.com/cloudflare.html',
    'https://ip.164746.xyz',
    'https://cf.vvhan.com/'
]

# 定义 IPv4 匹配正则表达式
ip_pattern = r'\d{1,3}(?:\.\d{1,3}){3}'

# 定义函数：判断 IP 地址是否合法
def is_valid_ip(ip):
    parts = ip.split('.')  # 按 . 分割为四段
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        num = int(part)
        if num < 0 or num > 255:
            return False
    # 排除一些无效地址
    if ip in ('0.0.0.0', '127.0.0.1', '255.255.255.255'):
        return False
    return True

# 定义函数：从指定 URL 中提取 IP 地址
def fetch_ips(url):
    ip_list = []  # 当前网站提取的 IP 列表
    try:
        print(f'🔍 正在请求：{url}')  # 提示请求开始
        response = requests.get(url, timeout=10)  # 10 秒超时，防止卡死
        soup = BeautifulSoup(response.text, 'html.parser')  # 解析 HTML

        # 处理 cf.vvhan.com 页面，IP 在 <td> 中
        if url == 'https://cf.vvhan.com/':
            elements = soup.find_all('td')  # 查找所有 td 标签
            for el in elements:
                text = el.get_text(strip=True)
                ip_list.extend(re.findall(ip_pattern, text))

        # 处理其他两个网页，IP 在 <tr> 标签中
        elif url in ('https://api.uouin.com/cloudflare.html', 'https://ip.164746.xyz'):
            elements = soup.find_all('tr')  # 查找所有表格行
            for el in elements:
                text = el.get_text(strip=True)
                ip_list.extend(re.findall(ip_pattern, text))

        # 默认处理方式：查找 <li> 标签
        else:
            elements = soup.find_all('li')
            for el in elements:
                text = el.get_text(strip=True)
                ip_list.extend(re.findall(ip_pattern, text))

        # 过滤掉无效 IP
        ip_list = [ip for ip in ip_list if is_valid_ip(ip)]

        print(f'✅ 成功提取 {len(ip_list)} 个 IP 来自：{url}')
        return ip_list  # 返回合法 IP 列表

    except requests.exceptions.RequestException as e:
        print(f'⚠️ 请求失败：{url} —— {e}')  # 请求错误
    except Exception as e:
        print(f'⚠️ 未知错误：{url} —— {e}')  # 其它错误
    return []  # 返回空列表防止程序中断

# 删除旧文件 ip.txt（如果存在）
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

# 使用集合存储所有 IP，自动去重
all_ips = set()

# 启用线程池并发请求，提升抓取效率
with ThreadPoolExecutor(max_workers=5) as executor:
    # 提交所有 URL 抓取任务
    future_to_url = {executor.submit(fetch_ips, url): url for url in urls}

    # 等待所有任务完成
    for future in as_completed(future_to_url):
        url = future_to_url[future]
        try:
            ips = future.result()  # 获取结果
            all_ips.update(ips)  # 添加到总集合中（自动去重）
        except Exception as e:
            print(f'❌ 抓取失败（{url}）：{e}')  # 报错提示

# 写入所有 IP 到 ip.txt 文件
try:
    with open('ip.txt', 'w') as file:
        for ip in sorted(all_ips):  # 排序后写入
            file.write(ip + '\n')
            print(f'📥 写入 IP：{ip}')
    print(f'🎉 总共提取 {len(all_ips)} 个有效 IP，已保存到 ip.txt。')
except Exception as e:
    print(f'❌ 写入文件失败：{e}')
