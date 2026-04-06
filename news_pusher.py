import feedparser
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from googletrans import Translator

PUSHPLUS_TOKEN = "这里填你的PushPlus token"   # ← 改成你的真实 token

translator = Translator()

def send_to_wechat(title, content):
    print(f"[推送] 标题: {title}")
    url = "https://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "html",
        "channel": "wechat"
    }
    try:
        resp = requests.post(url, json=data, timeout=10)
        print(f"[推送成功] 状态码: {resp.status_code} | 标题: {title[:50]}...")
    except Exception as e:
        print(f"[推送失败] 错误: {e}")

# ================== 极简 WSJ 测试 ==================
def fetch_wsj_news():
    print("[WSJ] 开始抓取...")
    rss_url = "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain"
    feed = feedparser.parse(rss_url)
    print(f"[WSJ] 抓到 {len(feed.entries)} 条新闻")
    
    for entry in feed.entries[:3]:   # 只取前3条测试
        try:
            title_cn = translator.translate(entry.title, dest='zh-cn').text
            print(f"[WSJ] 翻译成功: {title_cn[:60]}...")
            send_to_wechat(f"【WSJ测试】{title_cn}", "测试推送 - 请忽略此条")
        except Exception as e:
            print(f"[WSJ] 处理失败: {e}")

# ================== 极简 Moomoo 测试 ==================
def fetch_moomoo_news():
    print("[Moomoo] 开始抓取...")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get("https://www.moomoo.com/us/news", headers=headers, timeout=15)
        print(f"[Moomoo] 页面状态码: {resp.status_code}, 内容长度: {len(resp.text)}")
        print("[Moomoo] 抓取成功，但本次只测试WSJ，Moomoo暂不推送")
    except Exception as e:
        print(f"[Moomoo] 抓取失败: {e}")

# 主循环 - 只跑一次用于诊断
if __name__ == "__main__":
    print(f"[{datetime.now()}] === 诊断版启动 ===")
    fetch_wsj_news()
    fetch_moomoo_news()
    print(f"[{datetime.now()}] === 诊断运行结束 ===")
