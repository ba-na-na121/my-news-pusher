import time
from datetime import datetime

print(f"[{datetime.now()}] === 极简诊断版启动 ===")
print("如果看到这条消息，说明代码可以正常运行")
print("正在测试 PushPlus 推送...")

# 测试推送一条消息
try:
    import requests
    PUSHPLUS_TOKEN = "这里填你的PushPlus token"   # ←←← 改成你的真实 token
    
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": "测试推送 - 诊断版",
        "content": "如果收到这条消息，说明推送功能正常。\n\n当前时间：" + str(datetime.now()),
        "template": "html",
        "channel": "wechat"
    }
    resp = requests.post("https://www.pushplus.plus/send", json=data, timeout=10)
    print(f"推送请求已发送，状态码: {resp.status_code}")
except Exception as e:
    print(f"推送失败: {e}")

print(f"[{datetime.now()}] === 诊断运行结束 ===")
