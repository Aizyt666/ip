# 导入必要模块
import requests  # 发送网络请求
from bs4 import BeautifulSoup  # 解析 HTML 页面
import re  # 正则表达式，用于提取 IP
import os  # 文件与操作系统交互
from concurrent.futures import ThreadPoolExecutor, as_completed  # 多线程并发执行任务

# 定义包含目标网页的列表，每个网页都可能包含 Cloudflare 的 IP 列表
urls = [
    'https://api.uouin.com/cloudflare.html',
    'https://ip.164746.xyz',
    'https://cf.vvhan.com/'
]

# 正则表达式匹配 IPv4 地址（如 192.168.1.1）
ip_pattern = r'\d{1,3}(?:\.\d{1,3}){3}'

# 定义函数：判断一个 IP 地址是否合法
def is_valid_ip(ip):
    parts = ip.split('.')  # 将 IP 拆分为 4 段
    if len(parts) != 4:
        return False  # IP 段数不为 4 直接判为无效
    for part in parts:
        if not part.isdigit():  # 必须是数字
            return False
        num = int(part)
        if num < 0 or num > 255:  # 每段必须是 0～255
            return False
    # 排除一些特殊无效 IP
    if ip in ('0.0.0.0', '127.0.0.1', '255.255.255.255'):
        return False
    return True  # 通过全部验证，说明是合法 IP

# 定义主函数：从单个 URL 抓取 IP 地址（支持并发）
def fetch_ips(url):
    ip_list = []  # 用于存储该网址提取到的合法 IP
    try:
        print(f'🔍 正在请求：{url}')  # 提示当前正在请求哪个网站
        response = requests.get(url, timeout=10)  # 发送 GET 请求，10 秒超时防卡死
        soup = BeautifulSoup(response.text, 'html.parser')  # 用 BeautifulSoup 解析 HTML

        # 如果是 vvhan.com，IP 列表通常在 <textarea> 中
        if url == 'https://cf.vvhan.com/':
            textarea = soup.find('textarea')  # 查找 textarea 标签
            if textarea:
                content = textarea.get_text()  # 获取文本内容
                ip_list = re.findall(ip_pattern, content)  # 用正则找出所有 IP
        # 如果是其他两个已知结构的网站，IP 通常在 <tr> 表格中
        elif url in ('https://api.uouin.com/cloudflare.html', 'https://ip.164746.xyz'):
            elements = soup.find_all('tr')  # 查找所有表格行
            for el in elements:
                text = el.get_text()  # 提取文本
                ip_list.extend(re.findall(ip_pattern, text))  # 添加所有匹配的 IP
        else:
            # 默认情况：查找列表项 <li>
            elements = soup.find_all('li')
            for el in elements:
                text = el.get_text()
                ip_list.extend(re.findall(ip_pattern, text))

        # 过滤掉不合法的 IP
        ip_list = [ip for ip in ip_list if is_valid_ip(ip)]

        print(f'✅ 成功提取 {len(ip_list)} 个 IP 来自：{url}')  # 打印本网址提取成功的数量
        return ip_list  # 返回合法 IP 列表

    except requests.exceptions.RequestException as e:
        # 网络请求类错误（如超时、DNS失败等）
        print(f'⚠️ 请求失败：{url} —— {e}')
    except Exception as e:
        # 捕获其它所有异常，避免程序中断
        print(f'⚠️ 未知错误：{url} —— {e}')
    return []  # 出错时返回空列表

# 如果已存在 ip.txt 文件，则先删除，避免旧数据混杂
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

# 创建一个集合（自动去重）用于汇总所有网站抓取到的 IP
all_ips = set()

# 使用线程池进行并发请求，每个 URL 启动一个线程
with ThreadPoolExecutor(max_workers=5) as executor:
    # 提交所有任务，构造一个 future -> url 的映射表
    future_to_url = {executor.submit(fetch_ips, url): url for url in urls}
    
    # 遍历所有已完成的 future（请求任务）
    for future in as_completed(future_to_url):
        url = future_to_url[future]  # 获取对应网址
        try:
            ips = future.result()  # 获取线程函数返回的 IP 列表
            all_ips.update(ips)  # 添加到总集合中（自动去重）
        except Exception as e:
            print(f'❌ 抓取失败（{url}）：{e}')  # 捕获任何未预料的线程异常

# 写入所有 IP 到 ip.txt 文件，并同时在控制台打印
try:
    with open('ip.txt', 'w') as file:  # 打开文件准备写入
        for ip in sorted(all_ips):  # 排序后写入每个 IP
            file.write(ip + '\n')  # 写入文件
            print(f'📥 写入 IP：{ip}')  # 控制台打印每个 IP
    print(f'🎉 总共提取 {len(all_ips)} 个有效 IP，已保存到 ip.txt。')  # 提示提取完成
except Exception as e:
    print(f'❌ 写入文件失败：{e}')  # 如果文件写入失败，打印错误信息
