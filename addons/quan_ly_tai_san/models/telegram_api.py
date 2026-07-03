# -*- coding: utf-8 -*-
"""Kết nối External API: Telegram Bot (sendMessage)."""
import json
import urllib.request
import urllib.parse


def gui_tin_telegram(token, chat_id, noi_dung, timeout=20):
    if not token or not chat_id:
        return False
    url = "https://api.telegram.org/bot%s/sendMessage" % token
    du_lieu = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": noi_dung,
        "parse_mode": "HTML",
    }).encode("utf-8")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=du_lieu), timeout=timeout) as resp:
            kq = json.loads(resp.read().decode("utf-8"))
            return bool(kq.get("ok"))
    except Exception:
        return False
