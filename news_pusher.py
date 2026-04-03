import feedparser
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from googletrans import Translator

PUSHPLUS_TOKEN = "f585cce97ca04f04af1bd2b8ceb06e7f"

translator = Translator()

def send_to_wechat(title, content):
    url = "https://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "html",
        "channel": "wechat"
    }
    requests.post(url, json=data, timeout=10)

def add_label(title, summary):
    text = (title + " " + (summary or "")).lower()
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

# ================== 改进后的 WSJ 抓取（尝试获取更长内容） ==================
def fetch_wsj_news():
    rss_urls = [
        "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
        "https://feeds.content.dowjones.io/public/rss/RSSWorldNews"
    ]
    for rss_url in rss_urls:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:4]:
            try:
                label = add_label(entry.title, entry.summary if hasattr(entry, 'summary') else "")
                title_cn = translator.translate(entry.title, dest='zh-cn').text
                
                # 尝试获取更长的摘要
                summary = entry.summary if hasattr(entry, 'summary') else ""
                summary_cn = translator.translate(summary[:600], dest='zh-cn').text if summary else "暂无摘要"
                
                content = f"""
{summary_cn}

<br><br>
原文链接: <a href="{entry.link}">{entry.link}</a>
                """
                send_to_wechat(f"{label}【WSJ】{title_cn}", content.strip())
            except:
                pass

# ================== Moomoo 抓取 ==================
def fetch_moomoo_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get("https://www.moomoo.com/us/news", headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        articles = soup.find_all('div', class_=lambda x: x and ('news' in str(x).lower() or 'item' in str(x).lower()))[:6]
        
        for article in articles:
            title_tag = article.find(['h2', 'h3', 'a'])
            if not title_tag:
                continue
            title = title_tag.get_text().strip()
            link = title_tag.get('href')
            if not link.startswith('http'):
                link = "https://www.moomoo.com" + link
            
            try:
                label = add_label(title, "")
                title_cn = translator.translate(title, dest='zh-cn').text
                send_to_wechat(f"{label}【Moomoo】{title_cn}", f"链接: {link}")
            except:
                pass
    except Exception as e:
        print(f"Moomoo抓取失败: {e}")

# 主循环 - 每30分钟一次（推荐）
if __name__ == "__main__":
    print("改进版新闻推送机器人已启动（每30分钟一次）...")
    while True:
        print(f"[{datetime.now()}] 开始抓取新闻...")
        fetch_wsj_news()
        fetch_moomoo_news()
        print(f"[{datetime.now()}] 本轮完成，休息30分钟...\n")
        time.sleep(30 * 60)
