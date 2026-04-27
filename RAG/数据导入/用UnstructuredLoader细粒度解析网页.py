import requests
from bs4 import BeautifulSoup

page_url = "https://zh.wikipedia.org/wiki/黑神话：悟空"

# 添加请求头，模拟浏览器访问
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 下载网页
response = requests.get(page_url, headers=headers)
response.raise_for_status()

# 使用 BeautifulSoup 解析 HTML
soup = BeautifulSoup(response.text, 'html.parser')

# 提取主要内容（维基百科的正文通常在 #mw-content-text 中）
content = soup.find('div', {'id': 'mw-content-text'})

if content:
    # 提取所有段落文本
    paragraphs = content.find_all('p')
    
    print(f'找到 {len(paragraphs)} 个段落\n')
    print('=' * 80)
    
    # 打印前5个段落
    for i, p in enumerate(paragraphs[:5]):
        text = p.get_text(strip=True)
        if text:  # 只打印非空段落
            print(f'段落 {i+1}:')
            print(text)
            print('-' * 80)
else:
    print('未找到主要内容')
    # 打印页面标题作为备用
    title = soup.find('h1', {'id': 'firstHeading'})
    if title:
        print(f'页面标题: {title.get_text()}')