#!/usr/bin/env python3
import os
import sys
import time
import json
import hmac
import hashlib
import base64
import urllib.parse
import requests

def _build_weather_url(api_id, api_key, province, city):
    base = "https://cn.apihz.cn/api/tianqi/tqyb.php"
    params = {
        "id": api_id,
        "key": api_key,
        "sheng": province,
        "place": city
    }
    return base + "?" + urllib.parse.urlencode(params, safe='')

def _add_sign_to_webhook(webhook_url, secret):
    """
    If DINGTALK_SECRET is provided, append timestamp and sign to the webhook URL.
    Returns the signed webhook URL.
    """
    timestamp = str(int(round(time.time() * 1000)))
    string_to_sign = f"{timestamp}\n{secret}"
    h = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256)
    sign = base64.b64encode(h.digest()).decode('utf-8')
    sign_quoted = urllib.parse.quote_plus(sign)
    sep = '&' if '?' in webhook_url else '?'
    return f"{webhook_url}{sep}timestamp={timestamp}&sign={sign_quoted}"

def main():
    api_id = os.getenv("WEATHER_API_ID")
    api_key = os.getenv("WEATHER_API_KEY")
    province = os.getenv("PROVINCE", "安徽")
    city = os.getenv("CITY", "宣城")
    webhook = os.getenv("DINGTALK_WEBHOOK")
    secret = os.getenv("DINGTALK_SECRET", "")

    if not api_id or not api_key:
        print("ERROR: WEATHER_API_ID and WEATHER_API_KEY must be set.", file=sys.stderr)
        sys.exit(2)
    if not webhook:
        print("ERROR: DINGTALK_WEBHOOK must be set (store the full webhook URL as a GitHub Secret named DINGTALK_WEBHOOK).", file=sys.stderr)
        sys.exit(2)

    weather_url = _build_weather_url(api_id, api_key, province, city)
    print(f"Fetching weather from: {weather_url}")

    try:
        r = requests.get(weather_url, timeout=15)
    except Exception as e:
        print(f"ERROR: failed to GET weather API: {e}", file=sys.stderr)
        sys.exit(3)

    if r.status_code != 200:
        print(f"ERROR: weather API returned status {r.status_code}", file=sys.stderr)
        print("Response body:", r.text)
        sys.exit(4)

    try:
        weather_data = r.json()
        weather_text = json.dumps(weather_data, ensure_ascii=False, indent=2)
    except Exception:
        weather_text = r.text

    prefix = f"天气推送 — {province} {city}\n\n"
    content = prefix + weather_text
    if len(content) > 15000:
        content = content[:14990] + "\n\n...[truncated]"

    if secret:
        webhook = _add_sign_to_webhook(webhook, secret)

    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }

    headers = {"Content-Type": "application/json;charset=utf-8"}
    try:
        resp = requests.post(webhook, headers=headers, data=json.dumps(payload), timeout=15)
    except Exception as e:
        print(f"ERROR: failed to POST to DingTalk webhook: {e}", file=sys.stderr)
        sys.exit(5)

    print("DingTalk response status:", resp.status_code)
    try:
        resp_json = resp.json()
        print("DingTalk response JSON:", json.dumps(resp_json, ensure_ascii=False))
        if isinstance(resp_json, dict) and resp_json.get("errcode") == 0:
            print("Sent successfully.")
            sys.exit(0)
        else:
            print("DingTalk reported error.", file=sys.stderr)
            sys.exit(6)
    except ValueError:
        print("Non-JSON response from DingTalk:", resp.text)
        sys.exit(7)

if __name__ == "__main__":
    main()
