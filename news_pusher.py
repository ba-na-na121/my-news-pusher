import feedparser
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from googletrans import Translator

PUSHPLUS_TOKEN = "f585cce97ca04f04af1bd2b8ceb06e7f"

translator = Translator()

def send_to_wechat(title, content):
    print(f"准备推送: {title}")
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
        print(f"推送成功! 状态码: {resp.status_code}")
    except Exception as e:
        print(f"推送失败: {e}")

def add_label(title, summary=""):
    text = (title + " " + summary).lower()
    label = ""
    if any(k in text for k in ["breaking", "urgent", "just", "flash"]):
        label += "【Breaking】"
    if any(k in text for k in ["tesla", "spacex", "nvidia", "microsoft", "tsla"]):
        label += "【领头公司】"
    if any(k in text for k in ["ackman", "buffett", "trader"]):
        label += "【大交易员】"
    if any(k in text for k in ["trump", "伊朗", "iran", "tariff", "fed", "war", "hormuz"]):
        label += "【政治】"
    return label.strip() + " " if label else ""

# ================== WSJ 抓取 ==================
def fetch_wsj_news():
    print("开始抓取 WSJ 新闻...")
    rss_urls = [
        "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
        "https://feeds.content.dowjones.io/public/rss/RSSWorldNews"
    ]
    count = 0
    for rss_url in rss_urls:
        feed = feedparser.parse(rss_url)
        print(f"WSJ feed {rss_url} 共有 {len(feed.entries)} 条")
        for entry in feed.entries[:5]:
            try:
                label = add_label(entry.title, getattr(entry, 'summary', ''))
                title_cn = translator.translate(entry.title, dest='zh-cn').text
                summary = getattr(entry, 'summary', '')[:500]
                summary_cn = translator.translate(summary, dest='zh-cn').text if summary else "暂无摘要"
                
                content = f"{summary_cn}<br><br>原文: <a href='{entry.link}'>{entry.link}</a>"
                send_to_wechat(f"{label}【WSJ】{title_cn}", content)
                count += 1
            except Exception as e:
                print(f"WSJ 处理单条失败: {e}")
    print(f"WSJ 本轮处理完成，共尝试推送 {count} 条")

# ================== Moomoo 抓取（加强诊断） ==================
def fetch_moomoo_news():
    print("开始抓取 Moomoo 新闻...")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get("https://www.moomoo.com/us/news", headers=headers, timeout=20)
        print(f"Moomoo 页面状态码: {resp.status_code}, 长度: {len(resp.text)}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        articles = soup.find_all(['h1', 'h2', 'h3', 'article', 'div'])
        
        count = 0
        for article in articles[:20]:   # 扩大搜索范围
            text = article.get_text().strip()
            if len(text) > 15 and any(k in text.lower() for k in ["oil", "trump", "tesla", "iran", "stock", "market"]):
                try:
                    title_cn = translator.translate(text[:100], dest='zh-cn').text
                    send_to_wechat(f"【Moomoo】{title_cn[:60]}...", f"内容片段: {text[:200]}...")
                    count += 1
                except:
                    pass
        print(f"Moomoo 本轮找到并尝试推送 {count} 条")
    except Exception as e:
        print(f"Moomoo抓取失败: {e}")

# 主循环
if __name__ == "__main__":
    print(f"[{datetime.now()}] 诊断版新闻机器人启动...")
    fetch_wsj_news()
    fetch_moomoo_news()
    print(f"[{datetime.now()}] 本轮诊断运行完成")
    # 测试时只跑一次，正式用时改回 time.sleep(30*60)
