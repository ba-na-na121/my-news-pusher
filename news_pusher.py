import feedparser
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from googletrans import Translator

# ================== 配置区 ==================
PUSHPLUS_TOKEN = "f585cce97ca04f04af1bd2b8ceb06e7f"   # ←←← 改成你的真实 token

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

# ================== 智能标签逻辑 ==================
def add_label(title, summary):
    text = (title + " " + summary).lower()
    label = ""
    if any(k in text for k in ["breaking", "urgent", "just", "flash", "突发"]):
        label += "【Breaking】"
    if any(k in text for k in ["tesla", "spacex", "nvidia", "microsoft", "tsla", "领头", "龙头"]):
        label += "【领头公司】"
    if any(k in text for k in ["ackman", "buffett", "trader", "大佬", "大交易员", "position", "stake"]):
        label += "【大交易员】"
    if any(k in text for k in ["trump", "伊朗", "iran", "tariff", "fed", "政治", "war", "hormuz"]):
        label += "【政治】"
    return label.strip() + " " if label else ""

# ================== 抓取 WSJ（全部抓取） ==================
def fetch_wsj_news():
    rss_urls = [
        "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
        "https://feeds.content.dowjones.io/public/rss/RSSWorldNews"
    ]
    for rss_url in rss_urls:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:3]:   # 每源取3条最新
            try:
                label = add_label(entry.title, entry.summary if hasattr(entry, 'summary') else "")
                title_cn = translator.translate(entry.title, dest='zh-cn').text
                summary_cn = translator.translate(entry.summary[:400], dest='zh-cn').text if hasattr(entry, 'summary') else ""
                content = f"{summary_cn}<br><br>原文: <a href='{entry.link}'>{entry.link}</a>"
                send_to_wechat(f"{label}【WSJ】{title_cn}", content)
            except:
                pass

# ================== 抓取 Moomoo（全部抓取） ==================
def fetch_moomoo_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get("https://www.moomoo.com/us/news", headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        articles = soup.find_all('div', class_=lambda x: x and ('news' in str(x).lower() or 'item' in str(x).lower()))[:5]
        
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

# ================== 主循环 ==================
if __name__ == "__main__":
    print("全量新闻推送机器人已启动（每15分钟抓取一次）...")
    while True:
        print(f"[{datetime.now()}] 开始抓取所有最新新闻并打标签...")
        fetch_wsj_news()
        fetch_moomoo_news()
        print(f"[{datetime.now()}] 本轮完成，休息15分钟...\n")
        time.sleep(15 * 60)
