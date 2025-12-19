import feedparser
import requests
import json
import os
from datetime import datetime

# ================= 配置区 =================
# 精选 3 个互补的财经源，覆盖宏观、A股、港美股
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

# 从 GitHub Secrets 读取密钥
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
            # 设置超时时间，防止卡死
            feed = feedparser.parse(source['url'])
            
            if not feed.entries:
                print(f"⚠️ {source['name']} 暂时没有更新或抓取失败，跳过。")
                continue
                
            # 每个源只取前 4 条，防止文章过长
            combined_news += f"\n--- 来自 {source['name']} ---\n"
            for entry in feed.entries[:4]:
                title = entry.title
                # 简单清洗摘要
                summary = entry.summary[:100] if hasattr(entry, 'summary') else ""
                combined_news += f"• {title}\n"
                
        except Exception as e:
            print(f"❌ 抓取 {source['name']} 失败: {e}")
            
    return combined_news

def analyze_with_ai(text):
    """调用 DeepSeek 进行合规化舆情分析"""
    print("🧠 正在呼叫 DeepSeek 进行量化分析...")
    
    today_str = datetime.now().strftime('%m月%d日')
    
    # 🌟 合规安全版 Prompt (核心修改点)
    # 把“荐股”变成了“舆情监测”，规避法律风险，但保留了数据价值
    prompt = f"""
    你是一名“AI 量化舆情分析师”。你的任务是从海量财经新闻中提取“市场情绪”和“主力资金流向”线索，辅助投资者决策。
    请阅读以下资讯：
    {text}
    
    请输出一份《{today_str} AI 舆情量化日报》，严格遵守以下 Markdown 格式：

    # 📊 市场情绪温度计
    * **今日关键词**：(用3个词概括，如：#锂电爆发 #AI分歧 #避险升温)
    * **贪婪/恐慌指数**：(根据新闻内容打分，0-10分。0为极度恐慌，10为极度贪婪)

    # 🔥 热门风口 (只写 2 个最热板块或个股)
    
    ## 🚀 焦点 1：[板块或股票名]
    * **舆情热度**：⭐⭐⭐⭐⭐ (用星星表示)
    * **主力逻辑**：(用一句话概括新闻里提到的上涨/下跌逻辑，例如：机构大额净买入，受政策利好驱动)
    * **多空博弈**：(指出新闻中提到的关键价格或支撑/压力位数据，如果没有就写“情绪由空转多”或“资金净流出”)

    ## 🚀 焦点 2：[板块或股票名]
    * **舆情热度**：...
    * **主力逻辑**：...
    * **多空博弈**：...

    # 💡 潜伏线索 (Data Insight)
    * **AI 发现**：(挖掘一条容易被散户忽视的细节，比如某高管减持、某产品涨价等)

    **⚠️ 严格遵守：**
    1. **绝对禁止**使用“买入”、“卖出”、“加仓”、“推荐”等指导性字眼。
    2. 使用“关注”、“热度上升”、“资金流入”、“情绪乐观”等客观中性描述。
    3. 所有数据必须基于提供的新闻，不要编造。
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
    """推送到微信 (PushPlus)"""
    print("📨 正在推送到微信...")
    url = "http://www.pushplus.plus/send"
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 在消息底部加上免责声明，进一步降低风险
    disclaimer = "\n\n---\n⚠️ **免责声明**：\n本内容由 AI 程序自动生成，仅供市场舆情参考，不构成任何投资建议。市场有风险，投资需谨慎。"
    final_content = content + disclaimer
    
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": f"📈 舆情内参 {today}",
        "content": final_content,
        "template": "markdown"
    }
    
    try:
        resp = requests.post(url, json=payload)
        print("✅ 推送完成:", resp.text)
    except Exception as e:
        print(f"❌ 推送失败: {e}")

# ================= 主程序入口 =================
if __name__ == "__main__":
    # 1. 抓取多源数据
    raw_news = get_all_news()
    
    # 简单判断抓取内容长度，确保有足够信息给 AI
    if raw_news and len(raw_news) > 50: 
        # 2. AI 分析
        ai_report = analyze_with_ai(raw_news)
        
        if ai_report:
            # 3. 发送
            send_to_wechat(ai_report)
            print("🎉 今日任务圆满结束！")
        else:
            print("⚠️ AI 返回内容为空，取消发送。")
    else:
        print("⚠️ 未抓取到有效新闻（可能源暂时无法访问），请稍后重试。")
