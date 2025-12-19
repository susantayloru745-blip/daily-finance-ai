import feedparser
import requests
import json
import os
from datetime import datetime

# ================= 配置区 =================
# 1. 你的 RSS 源 (使用你之前测试成功的 rssforever 镜像)
RSS_URL = "https://rsshub.rssforever.com/wallstreetcn/hot"

# 2. 从 GitHub 设置里读取密钥 (不要改这里)
API_KEY = os.environ.get("DEEPSEEK_API_KEY") 
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN")

# DeepSeek 接口地址
API_URL = "https://api.deepseek.com/chat/completions"

# ================= 功能函数 =================

def get_rss_news():
    """抓取 RSS 新闻"""
    print("正在抓取 RSS 数据...")
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            print("❌ 未抓取到任何新闻，请检查 RSS 链接是否失效。")
            return None
            
        news_list = []
        # 只取前 5 条，防止内容太长 AI 处理不了
        for entry in feed.entries[:5]:
            title = entry.title
            #有些RSS摘要可能有HTML标签，简单清洗一下，或者直接用摘要
            summary = entry.summary[:150] if hasattr(entry, 'summary') else "无摘要"
            news_list.append(f"【标题】{title}\n【摘要】{summary}\n")
            
        return "\n---\n".join(news_list)
    except Exception as e:
        print(f"❌ 抓取出错: {e}")
        return None

def analyze_with_ai(text):
    """调用 DeepSeek 进行分析"""
    print("正在呼叫 DeepSeek 分析师...")
    
    # 这里是你的核心指令 (Prompt)
    prompt = f"""
    你是一名毒舌且专业的华尔街交易员。请阅读以下今日财经热点：
    {text}
    
    任务：
    1. 筛选出 3 个真正重要的新闻（忽略凑数的）。
    2. 用通俗、犀利的语言点评（一针见血，不要废话）。
    3. 明确指出：这对 A股/美股/加密货币 是【利好】还是【利空】。
    4. 格式要求：使用 Markdown 格式，重点内容加粗。
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ AI 分析出错: {e}")
        return "AI 罢工了，请检查 API Key 或 余额。"

def send_to_wechat(content):
    """推送到微信 (通过 PushPlus)"""
    print("正在推送到微信...")
    url = "http://www.pushplus.plus/send"
    
    # 今天的日期
    today = datetime.now().strftime('%Y-%m-%d')
    
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": f"💰 财经早报 {today}", # 微信消息标题
        "content": content,
        "template": "markdown" # 启用 Markdown 模式，排版更好看
    }
    
    try:
        resp = requests.post(url, json=payload)
        print("✅ 推送结果:", resp.text)
    except Exception as e:
        print(f"❌ 推送失败: {e}")

# ================= 主程序入口 =================
if __name__ == "__main__":
    # 1. 抓新闻
    raw_news = get_rss_news()
    
    if raw_news:
        # 2. AI 分析
        ai_report = analyze_with_ai(raw_news)
        
        # 3. 发微信
        # 可以在这里加个页脚
        final_content = ai_report + "\n\n---\n🤖 本日报由 DeepSeek AI 自动生成"
        send_to_wechat(final_content)
        print("🎉 全部任务执行完毕！")
    else:
        print("⚠️ 没有新闻可供分析，跳过后续步骤。")
