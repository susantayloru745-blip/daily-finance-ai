import feedparser
import requests
import json
import os
from datetime import datetime

# ================= 配置区 (这里升级了!) =================
# 我们精选了 3 个互补的源，覆盖全市场
RSS_SOURCES = [
    {
        "name": "🌊 华尔街见闻 (全球宏观)",
        "url": "https://rsshub.rssforever.com/wallstreetcn/live/global"
    },
    {
        "name": "🇨🇳 财联社 (A股电报)",
        "url": "https://rsshub.rssforever.com/cls/telegraph"
    },
    {
        "name": "🇺🇸 格隆汇 (美股/港股)",
        "url": "https://rsshub.rssforever.com/gelonghui/live"
    }
]

# 密钥配置 (不用动)
API_KEY = os.environ.get("DEEPSEEK_API_KEY") 
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN")
API_URL = "https://api.deepseek.com/chat/completions"

# ================= 功能函数 =================

def get_all_news():
    """抓取所有源的新闻并汇总"""
    print("🚀 开始全网扫描...")
    combined_news = ""
    
    for source in RSS_SOURCES:
        print(f"正在抓取: {source['name']}...")
        try:
            feed = feedparser.parse(source['url'])
            if not feed.entries:
                print(f"⚠️ {source['name']} 暂时没有更新，跳过。")
                continue
                
            # 每个源只取前 4 条，防止文章过长 DeepSeek 消化不良
            combined_news += f"\n--- 来自 {source['name']} ---\n"
            for entry in feed.entries[:4]:
                title = entry.title
                # 清洗摘要，去掉HTML标签
                summary = entry.summary[:100] if hasattr(entry, 'summary') else ""
                combined_news += f"• {title}\n"
                
        except Exception as e:
            print(f"❌ 抓取 {source['name']} 失败: {e}")
            
    return combined_news

def analyze_with_ai(text):
    """调用 DeepSeek 专家模式"""
    print("🧠 正在呼叫 DeepSeek 基金经理进行深度分析...")
    
    # 升级版 Prompt：更强调策略和逻辑
    today_str = datetime.now().strftime('%m月%d日')
    
    prompt = f"""
    你是一名拥有 20 年经验的华尔街对冲基金经理，擅长通过碎片化信息发现主力资金动向。
    请阅读以下来自多个渠道的财经资讯：
    {text}
    
    请为你的 VIP 客户撰写一份《{today_str} 市场操盘内参》，严格遵守以下 Markdown 格式：

    # 🦅 {today_str} 市场风向标

    ## 🚨 核心预警 (仅 1 条)
    * **一句话说清当下最大的风险或机会。** (例如：美联储鹰派发言，成长股注意回调)

    ## 💰 资金暗流 (精选 3 个关键点)
    * **[利好/利空/观望] 新闻标题**
      > **深度逻辑**：不要复述新闻！告诉我主力在干什么？这对散户意味着什么？(语气要毒舌、犀利)

    ## 🎯 操盘建议 (Actionable Advice)
    * **A股**：(一句话策略，如：轻仓博弈/空仓看戏)
    * **美股/加密**：(一句话策略)

    **要求：**
    1. 必须使用 Emoji 图标增加可读性。
    2. 过滤掉无意义的通稿，只保留有交易价值的信息。
    3. 语气要像在私募核心群里讲话，不要像新闻联播。
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
        return None

def send_to_wechat(content):
    """推送到微信"""
    print("📨 正在推送到微信...")
    url = "http://www.pushplus.plus/send"
    today = datetime.now().strftime('%Y-%m-%d')
    
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": f"📈 华尔街内参 {today}",
        "content": content,
        "template": "markdown"
    }
    
    try:
        resp = requests.post(url, json=payload)
        print("✅ 推送完成:", resp.text)
    except Exception as e:
        print(f"❌ 推送失败: {e}")

# ================= 主程序 =================
if __name__ == "__main__":
    # 1. 抓取多源数据
    raw_news = get_all_news()
    
    if raw_news and len(raw_news) > 20: # 确保抓到了足够的内容
        # 2. AI 分析
        ai_report = analyze_with_ai(raw_news)
        
        if ai_report:
            # 3. 发送
            send_to_wechat(ai_report)
            print("🎉 今日任务圆满结束！")
        else:
            print("⚠️ AI 返回为空，不发送。")
    else:
        print("⚠️ 未抓取到有效新闻，请检查网络或源。")
