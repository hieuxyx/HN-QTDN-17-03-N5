# -*- coding: utf-8 -*-
"""Kết nối External API: Google Gemini (generativelanguage REST v1beta).

Đọc/gọi bằng thư viện chuẩn (urllib) nên không cần cài thêm gói.
Dùng cho: OCR hóa đơn (đầu vào ảnh) và Trợ lý hỏi-đáp (đầu vào văn bản).
"""
import json
import urllib.request
import urllib.error

_DIEM_CUOI = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"


def goi_gemini(api_key, model, prompt, anh_base64=None, anh_mime="image/jpeg",
               json_output=False, timeout=60):
    if not api_key:
        raise ValueError("Chưa cấu hình Gemini API key.")
    parts = [{"text": prompt}]
    if anh_base64:
        parts.append({"inline_data": {"mime_type": anh_mime, "data": anh_base64}})
    body = {"contents": [{"parts": parts}]}
    if json_output:
        body["generationConfig"] = {"responseMimeType": "application/json"}
    du_lieu = json.dumps(body).encode("utf-8")
    url = _DIEM_CUOI % (model or "gemini-2.5-flash")
    req = urllib.request.Request(
        url, data=du_lieu, method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ket_qua = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        chi_tiet = e.read().decode("utf-8", "ignore")
        raise ValueError("Gemini API lỗi %s: %s" % (e.code, chi_tiet[:300]))
    except Exception as e:
        raise ValueError("Không gọi được Gemini API: %s" % e)
    try:
        return ket_qua["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise ValueError("Gemini không trả về nội dung hợp lệ.")
