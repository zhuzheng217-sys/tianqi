import os
import time
import json
import hmac
import hashlib
import base64
import urllib.parse
import requests


def sign_webhook(webhook, secret):
    timestamp = str(int(time.time() * 1000))

    string_to_sign = f"{timestamp}\n{secret}"

    hmac_code = hmac.new(
        secret.encode(),
        string_to_sign.encode(),
        hashlib.sha256
    ).digest()

    sign = urllib.parse.quote_plus(
        base64.b64encode(hmac_code).decode()
    )

    return f"{webhook}&timestamp={timestamp}&sign={sign}"


def fetch_weather():

    api_id = os.getenv("WEATHER_API_ID")
    api_key = os.getenv("WEATHER_API_KEY")

    province = os.getenv("PROVINCE", "安徽")
    city = os.getenv("CITY", "宣城")

    url = "https://cn.apihz.cn/api/tianqi/tqyb.php"

    params = {
        "id": api_id,
        "key": api_key,
        "sheng": province,
        "place": city
    }

    r = requests.get(url, params=params, timeout=15)

    if r.status_code != 200:
        return None

    try:
        data = r.json()
    except:
        return None

    # 判断数据是否有效
    if data.get("code") != 200:
        return None

    return data


def get_weather_with_retry():

    max_retry = 10

    for i in range(max_retry):

        print(f"尝试获取天气 {i+1}/{max_retry}")

        data = fetch_weather()

        if data:
            print("获取天气成功")
            return data

        if i < max_retry - 1:
            print("获取失败，30秒后重试...")
            time.sleep(30)

    print("天气API连续失败")
    return None


def send_dingtalk(msg):

    webhook = os.getenv("DINGTALK_WEBHOOK")
    secret = os.getenv("DINGTALK_SECRET")

    if secret:
        webhook = sign_webhook(webhook, secret)

    headers = {"Content-Type": "application/json"}

    r = requests.post(webhook, headers=headers, json=msg)

    print("DingTalk:", r.text)


def main():

    data = get_weather_with_retry()

    if not data:

        text = "⚠ 天气接口连续10次获取失败"

        msg = {
            "msgtype": "text",
            "text": {
                "content": text
            }
        }

        send_dingtalk(msg)

        return

    city = data.get("name", "未知")

    weather = data.get("weather1", "未知")

    high = data.get("wd1", "")
    low = data.get("wd2", "")

    wind_dir = data.get("winddirection1", "")
    wind_level = data.get("windleve1", "")

    now = data.get("nowinfo", {})

    temp_now = now.get("temperature", "")
    humidity = now.get("humidity", "")
    feel = now.get("feelst", "")

    text = f"""
🌤 {city}天气

天气：{weather}

当前温度：{temp_now}℃
体感温度：{feel}℃

今日温度：{low}℃ ~ {high}℃

风向：{wind_dir}
风力：{wind_level}

湿度：{humidity}%
"""

    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"{city}天气",
            "text": text
        }
    }

    send_dingtalk(msg)


if __name__ == "__main__":
    main()
