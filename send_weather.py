import os
import time
import json
import hmac
import hashlib
import base64
import urllib.parse
import requests


def build_weather_url(api_id, api_key, province, city):
    base = "https://cn.apihz.cn/api/tianqi/tqyb.php"
    params = {
        "id": api_id,
        "key": api_key,
        "sheng": province,
        "place": city
    }
    return base + "?" + urllib.parse.urlencode(params)


def sign_webhook(webhook, secret):
    timestamp = str(int(time.time() * 1000))

    string_to_sign = f"{timestamp}\n{secret}"

    hmac_code = hmac.new(
        secret.encode(),
        string_to_sign.encode(),
        hashlib.sha256
    ).digest()

    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

    return f"{webhook}&timestamp={timestamp}&sign={sign}"


def main():

    api_id = os.getenv("WEATHER_API_ID")
    api_key = os.getenv("WEATHER_API_KEY")

    province = os.getenv("PROVINCE", "安徽")
    city = os.getenv("CITY", "宣城")

    webhook = os.getenv("DINGTALK_WEBHOOK")
    secret = os.getenv("DINGTALK_SECRET")

    weather_url = build_weather_url(api_id, api_key, province, city)

    r = requests.get(weather_url, timeout=15)

    try:
        weather = r.json()
        text = json.dumps(weather, ensure_ascii=False, indent=2)
    except:
        text = r.text

    content = f"""
天气推送

地区：{province} {city}

{text}
"""

    if secret:
        webhook = sign_webhook(webhook, secret)

    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }

    headers = {"Content-Type": "application/json"}

    resp = requests.post(webhook, headers=headers, json=payload)

    print("status:", resp.status_code)
    print(resp.text)


if __name__ == "__main__":
    main()
