import os, json
import openai
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

TZ_UTC = ZoneInfo("UTC")
TZ_TPE = ZoneInfo("Asia/Taipei")

def parse_reminder(text: str) -> dict:
    """解析提醒指令，回傳經過時區轉換後的 {'event':…, 'time':…}"""
    now_str = datetime.now(TZ_TPE).strftime("%Y-%m-%d %H:%M:%S")
    system = (
        f"現在是台北時間 {now_str}，請將使用者的中文提醒指令解析為 JSON，"
        "格式：{\"event\":\"提醒內容\",\"time\":\"ISO 8601 時間格式\"}，只回傳 JSON。"
    )
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":system},
            {"role":"user",  "content":text}
        ],
        temperature=0.2
    )
    content = resp.choices[0].message.content.strip()
    if content.startswith("```"):
        content = "\n".join(content.splitlines()[1:-1])
    parsed = json.loads(content)

    # --------- 新增這段：UTC → 台北時間 ---------
    # 1. 先把 GPT 回傳的時間字串 parse 出來
    dt_utc = datetime.fromisoformat(parsed["time"])
    # 2. 標記為 UTC 時區
    dt_utc = dt_utc.replace(tzinfo=TZ_UTC)
    # 3. 轉成台北時區
    dt_tpe = dt_utc.astimezone(TZ_TPE)
    # 4. 再覆寫 parsed["time"]
    parsed["time"] = dt_tpe.isoformat()
    # -----------------------------------------

    return parsed

def classify_intent(text: str) -> bool:
    """判斷是否為提醒指令，回傳 True/False"""
    prompt = (
        "請判斷以下中文句子是否為提醒設定指令，"
        "只回傳 JSON: {\"is_reminder\": true} 或 {\"is_reminder\": false}，"
        f"句子：\"{text}\""
    )
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    j = json.loads(resp.choices[0].message.content.strip())
    return j.get("is_reminder", False)


def parse_reminder(text: str) -> dict:
    """解析提醒指令，回傳 {'event':..., 'time':...}"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system = (
        f"今天是 {now_str}，請將使用者的中文提醒指令解析為 JSON，"
        "格式：{\"event\":\"提醒內容\",\"time\":\"ISO 8601 時間格式\"}，只回傳 JSON。"
    )
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system},
                  {"role":"user","content":text}],
        temperature=0.2
    )
    content = resp.choices[0].message.content.strip()
    if content.startswith("```"):
        # 去掉 Markdown code block 標記
        content = "\n".join(content.splitlines()[1:-1])
    return json.loads(content)


def chat_reply(user_id: str, text: str) -> str:
    """一般聊天回覆"""
    messages = [
        {"role": "system", "content": "你是一個友善的聊天助理，當使用者不是設定提醒時，就用自然語言回覆他。"},
        {"role": "user",   "content": text}
    ]
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )
    return resp.choices[0].message.content.strip()

# services/llm_service.py  (在現有函式下方加入)

def classify_history(text: str) -> bool:
    """
    判斷使用者輸入是否想查看提醒歷史列表，
    回傳 True/False。
    """
    prompt = (
        "請判斷以下中文句子是否為「查看提醒歷史列表」的意圖，"
        "只回傳 JSON 格式：{\"is_history\": true} 或 {\"is_history\": false}，"
        f"句子：\"{text}\""
    )
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    j = json.loads(resp.choices[0].message.content.strip())
    return j.get("is_history", False)

# services/llm_service.py

def classify_pending(text: str) -> bool:
    """
    判斷使用者是否想看「尚未觸發提醒」列表，
    回傳 True/False。
    """
    prompt = (
        "請判斷以下中文句子是否為「想查看尚未觸發的提醒事項」的意圖，"
        "只回傳 JSON: {\"is_pending\": true} 或 {\"is_pending\": false}，"
        f"句子：\"{text}\""
    )
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    j = json.loads(resp.choices[0].message.content.strip())
    return j.get("is_pending", False)

