import feedparser
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from googletrans import Translator

PUSHPLUS_TOKEN = "这里填你的PushPlus token"   # ← 改成你的真实 token

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

def add_label(title, summary=""):
    text = (title + " " + summary).lower()
    label = ""
    if any(k in text for k in ["breaking", "urgent", "just", "flash", "突发"]):
        label += "【Breaking】"
    if any(k in text for k in ["tesla", "spacex", "nvidia", "microsoft", "tsla"]):
        label += "【领头公司】"
    if any(k in text for k in ["ackman", "buffett", "trader", "大佬"]):
        label += "【大交易员】"
    if any(k in text for k in ["trump", "伊朗", "iran", "tariff", "fed", "war", "hormuz", "政治"]):
        label += "【政治】"
    return label.strip() + " " if label else ""

# ================== WSJ 抓取（保持不变，内容较完整） ==================
def fetch_wsj_news():
    rss_urls = [
        "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
        "https://feeds.content.dowjones.io/public/rss/RSSWorldNews"
    ]
    for rss_url in rss_urls:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:4]:
            try:
                label = add_label(entry.title, getattr(entry, 'summary', ''))
                title_cn = translator.translate(entry.title, dest='zh-cn').text
                summary = getattr(entry, 'summary', '')[:600]
                summary_cn = translator.translate(summary, dest='zh-cn').text if summary else "暂无摘要"
                
                content = f"{summary_cn}<br><br>原文链接: <a href='{entry.link}'>{entry.link}</a>"
                send_to_wechat(f"{label}【WSJ】{title_cn}", content)
            except:
                pass

# ================== 加强版 Moomoo 抓取（解决抓不到的问题） ==================
def fetch_moomoo_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get("https://www.moomoo.com/us/news", headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 多种可能的选择器（提高成功率）
        selectors = [
            'div.news-item', 'div.news-card', 'article', 
            'div[class*="news"]', 'div[class*="item"]'
        ]
        
        articles = []
        for sel in selectors:
            found = soup.select(sel)
            if found:
                articles.extend(found)
                if len(articles) >= 8:
                    break
        
        articles = articles[:8]  # 最多取8条
        
        for article in articles:
            title_tag = article.find(['h1', 'h2', 'h3', 'a'])
            if not title_tag or len(title_tag.get_text().strip()) < 5:
                continue
                
            title = title_tag.get_text().strip()
            link = title_tag.get('href') or article.get('href')
            if link and not link.startswith('http'):
                link = "https://www.moomoo.com" + link
            
            try:
                label = add_label(title)
                title_cn = translator.translate(title, dest='zh-cn').text
                send_to_wechat(f"{label}【Moomoo】{title_cn}", f"链接: {link}")
                print(f"Moomoo推送成功: {title[:30]}...")
            except:
                pass
                
    except Exception as e:
        print(f"Moomoo抓取失败: {e}")

# ================== 主循环 ==================
if __name__ == "__main__":
    print("全量新闻推送机器人已启动（每30分钟一次）...")
    while True:
        print(f"[{datetime.now()}] 开始抓取 WSJ + Moomoo 新闻...")
        fetch_wsj_news()
        fetch_moomoo_news()
        print(f"[{datetime.now()}] 本轮完成，休息30分钟...\n")
        time.sleep(30 * 60)
