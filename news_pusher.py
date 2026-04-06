import feedparser
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from googletrans import Translator

# ================== 配置区 ==================
PUSHPLUS_TOKEN = "这里填你的PushPlus token"   # ←←← 改成你的真实 token

translator = Translator()

# 去重文件（自动创建）
SENT_FILE = "sent_links.txt"

def load_sent_links():
    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_sent_link(link):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

sent_links = load_sent_links()

def send_to_wechat(title, content, link):
    if link in sent_links:
        return False  # 已推送过，跳过
    url = "https://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "html",
        "channel": "wechat"
    }
    try:
        requests.post(url, json=data, timeout=10)
        save_sent_link(link)      # 记录已推送
        sent_links.add(link)
        print(f"推送成功: {title}")
        return True
    except Exception as e:
        print(f"推送失败: {e}")
        return False

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

# ================== WSJ 抓取 ==================
def fetch_wsj_news():
    rss_urls = [
        "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
        "https://feeds.content.dowjones.io/public/rss/RSSWorldNews"
    ]
    for rss_url in rss_urls:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:5]:
            link = entry.link
            if link in sent_links:
                continue
            try:
                label = add_label(entry.title, getattr(entry, 'summary', ''))
                title_cn = translator.translate(entry.title, dest='zh-cn').text
                summary = getattr(entry, 'summary', '')[:600]
                summary_cn = translator.translate(summary, dest='zh-cn').text if summary else "暂无摘要"
                
                content = f"{summary_cn}<br><br>原文链接: <a href='{link}'>{link}</a>"
                send_to_wechat(f"{label}【WSJ】{title_cn}", content, link)
            except:
                pass

# ================== Moomoo 抓取 ==================
def fetch_moomoo_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get("https://www.moomoo.com/us/news", headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        articles = soup.find_all(['h1', 'h2', 'h3', 'article', 'div'])[:15]
        
        for article in articles:
            title_tag = article.find(['h1', 'h2', 'h3', 'a'])
            if not title_tag:
                continue
            title = title_tag.get_text().strip()
            link = title_tag.get('href')
            if not link:
                continue
            if not link.startswith('http'):
                link = "https://www.moomoo.com" + link
            if link in sent_links:
                continue
                
            try:
                label = add_label(title)
                title_cn = translator.translate(title, dest='zh-cn').text
                send_to_wechat(f"{label}【Moomoo】{title_cn}", f"链接: {link}", link)
            except:
                pass
    except Exception as e:
        print(f"Moomoo抓取失败: {e}")

# ================== 主循环（每30分钟一次） ==================
if __name__ == "__main__":
    print("去重版新闻推送机器人已启动（每30分钟一次）...")
    while True:
        print(f"[{datetime.now()}] 开始抓取并去重推送...")
        fetch_wsj_news()
        fetch_moomoo_news()
        print(f"[{datetime.now()}] 本轮完成，休息30分钟...\n")
        time.sleep(30 * 60)
