import os
import time
import hmac
import json
import hashlib
import base64
import urllib.parse
import requests


def sign_webhook(webhook, secret):

    timestamp = str(int(time.time() * 1000))

    string_to_sign = f"{timestamp}\n{secret}"

    hmac_code = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256
    ).digest()

    sign = urllib.parse.quote_plus(
        base64.b64encode(hmac_code).decode()
    )

    return f"{webhook}&timestamp={timestamp}&sign={sign}"


def get_weather():

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

    r = requests.get(url, params=params)

    return r.json()


def send_dingtalk(msg):

    webhook = os.getenv("DINGTALK_WEBHOOK")
    secret = os.getenv("DINGTALK_SECRET")

    if secret:
        webhook = sign_webhook(webhook, secret)

    headers = {
        "Content-Type": "application/json"
    }

    r = requests.post(webhook, headers=headers, json=msg)

    print(r.text)


def main():

    data = get_weather()

    province = os.getenv("PROVINCE", "安徽")
    city = os.getenv("CITY", "宣城")

    weather = data.get("weather", "未知")
    temp = data.get("temperature", "未知")
    wind = data.get("wind", "未知")
    humidity = data.get("humidity", "未知")

    text = f"""
### 🌤 {city}天气

当前天气：{weather}

温度：{temp}

风力：{wind}

湿度：{humidity}
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
