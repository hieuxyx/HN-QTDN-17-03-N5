# -*- coding: utf-8 -*-
"""Trợ lý AI phân loại tài sản.

Gợi ý NHÓM tài sản từ tên/mô tả, dùng Machine Learning (phân loại văn bản).
- Nếu môi trường có scikit-learn -> dùng TF-IDF + Multinomial Naive Bayes.
- Nếu không -> tự cài đặt Naive Bayes thuần Python (không phụ thuộc thư viện ngoài).

Lưu ý: KHÔNG import thư viện nặng ở cấp module (sklearn được import "lười" bên
trong hàm) để việc cài đặt/khởi động Odoo không bị ảnh hưởng.
"""

import re
import math
from collections import defaultdict

# --- Dữ liệu mầm: nhãn loại tài sản -> ví dụ/từ khoá tiếng Việt ---
SEED_DATA = {
    "Thiết bị IT": [
        "laptop", "máy tính", "máy tính xách tay", "máy in", "máy quét",
        "màn hình", "máy chủ", "server", "router", "switch", "máy chiếu",
        "ổ cứng", "bàn phím", "chuột máy tính", "webcam", "máy photocopy", "ups",
    ],
    "Máy móc thiết bị": [
        "máy phát điện", "máy nén khí", "máy tiện", "máy phay",
        "dây chuyền sản xuất", "máy đóng gói", "máy bơm", "máy hàn",
        "máy cắt", "động cơ", "máy ép",
    ],
    "Phương tiện vận tải": [
        "ô tô", "xe ô tô", "xe tải", "xe máy", "xe nâng", "xe con",
        "xe khách", "xe bán tải", "xe đầu kéo",
    ],
    "Nội thất văn phòng": [
        "bàn làm việc", "ghế", "ghế xoay", "tủ tài liệu", "kệ", "bàn họp",
        "sofa", "tủ", "bàn", "giá sách",
    ],
    "Nhà cửa, vật kiến trúc": [
        "nhà xưởng", "nhà kho", "tòa nhà", "văn phòng", "công trình",
        "nhà điều hành",
    ],
}

# Gợi ý số kỳ khấu hao (tháng) theo nhãn — tham khảo khung Thông tư 45/2013/TT-BTC
SUGGESTED_MONTHS = {
    "Thiết bị IT": 36,
    "Máy móc thiết bị": 96,
    "Phương tiện vận tải": 72,
    "Nội thất văn phòng": 60,
    "Nhà cửa, vật kiến trúc": 240,
}

_TOKEN_RE = re.compile(r"[a-zA-ZÀ-ỹ0-9]+", re.UNICODE)


def _tokenize(text):
    return _TOKEN_RE.findall((text or "").lower())


def _build_corpus(extra_samples=None):
    """Gộp dữ liệu mầm + dữ liệu học thêm (tên tài sản đã có -> nhóm)."""
    texts, labels = [], []
    for label, samples in SEED_DATA.items():
        for s in samples:
            texts.append(s)
            labels.append(label)
    for text, label in (extra_samples or []):
        if text and label:
            texts.append(text)
            labels.append(label)
    return texts, labels


class _PurePythonNB:
    """Multinomial Naive Bayes thuần Python (không cần thư viện ngoài)."""

    def __init__(self):
        self.class_word_counts = defaultdict(lambda: defaultdict(int))
        self.class_counts = defaultdict(int)
        self.vocab = set()

    def fit(self, texts, labels):
        for text, label in zip(texts, labels):
            self.class_counts[label] += 1
            for tok in _tokenize(text):
                self.class_word_counts[label][tok] += 1
                self.vocab.add(tok)
        return self

    def predict_proba(self, text):
        tokens = _tokenize(text)
        total_docs = sum(self.class_counts.values()) or 1
        vocab_size = len(self.vocab) or 1
        log_scores = {}
        for label in self.class_counts:
            logp = math.log(self.class_counts[label] / total_docs)
            total_words = sum(self.class_word_counts[label].values())
            for tok in tokens:
                count = self.class_word_counts[label].get(tok, 0)
                logp += math.log((count + 1) / (total_words + vocab_size))  # Laplace
            log_scores[label] = logp
        if not log_scores:
            return {}
        mx = max(log_scores.values())
        exp = {k: math.exp(v - mx) for k, v in log_scores.items()}
        z = sum(exp.values()) or 1
        return {k: v / z for k, v in exp.items()}


def _train(extra_samples=None):
    texts, labels = _build_corpus(extra_samples)
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.pipeline import Pipeline
        model = Pipeline([
            ("tfidf", TfidfVectorizer(token_pattern=r"[a-zA-ZÀ-ỹ0-9]+",
                                      ngram_range=(1, 2))),
            ("clf", MultinomialNB()),
        ])
        model.fit(texts, labels)

        def predict_proba(text):
            probs = model.predict_proba([text or ""])[0]
            return dict(zip(model.classes_, probs))

        return predict_proba, "scikit-learn (TF-IDF + MultinomialNB)"
    except Exception:
        nb = _PurePythonNB().fit(texts, labels)
        return nb.predict_proba, "Naive Bayes (thuần Python)"


def suggest(text, extra_samples=None):
    """Trả về gợi ý nhãn loại tài sản, độ tin cậy (%), số kỳ khấu hao đề xuất.

    extra_samples: list các (tên_tài_sản, tên_nhóm) để mô hình học thêm từ dữ
    liệu thực tế trong hệ thống.
    """
    predict_proba, backend = _train(extra_samples)
    probs = predict_proba(text or "")
    if not probs:
        return {"label": None, "confidence": 0.0, "months": None,
                "backend": backend, "ranking": []}
    ranking = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    label, conf = ranking[0]
    return {
        "label": label,
        "confidence": round(float(conf) * 100, 1),
        "months": SUGGESTED_MONTHS.get(label),
        "backend": backend,
        "ranking": [(l, round(float(p) * 100, 1)) for l, p in ranking[:3]],
    }
