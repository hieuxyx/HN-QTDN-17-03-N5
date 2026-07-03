# -*- coding: utf-8 -*-
"""Trợ lý AI phân loại tài sản (offline) - Naive Bayes phân loại văn bản."""
import re
import math

DU_LIEU_MAM = {
    "Thiết bị IT": ["laptop", "máy tính", "máy tính xách tay", "máy in", "máy quét",
                    "màn hình", "máy chủ", "server", "router", "switch", "máy chiếu",
                    "ổ cứng", "bàn phím", "chuột máy tính", "webcam", "máy photocopy", "ups"],
    "Máy móc thiết bị": ["máy phát điện", "máy nén khí", "máy tiện", "máy phay",
                         "dây chuyền sản xuất", "máy đóng gói", "máy bơm", "máy hàn",
                         "máy cắt", "động cơ", "máy ép"],
    "Phương tiện vận tải": ["ô tô", "xe ô tô", "xe tải", "xe máy", "xe nâng", "xe con",
                            "xe khách", "xe bán tải", "xe đầu kéo"],
    "Nội thất văn phòng": ["bàn làm việc", "ghế", "ghế xoay", "tủ tài liệu", "kệ", "bàn họp",
                           "sofa", "tủ", "bàn", "giá sách"],
    "Nhà cửa, vật kiến trúc": ["nhà xưởng", "nhà kho", "tòa nhà", "văn phòng", "công trình",
                               "nhà điều hành"],
}
SO_KY_GOI_Y = {"Thiết bị IT": 36, "Máy móc thiết bị": 96, "Phương tiện vận tải": 72,
               "Nội thất văn phòng": 60, "Nhà cửa, vật kiến trúc": 240}
MA_NHOM = {"Thiết bị IT": "IT", "Máy móc thiết bị": "MMTB", "Phương tiện vận tải": "PTVT",
           "Nội thất văn phòng": "NTVP", "Nhà cửa, vật kiến trúc": "NCKT"}


def _tach_tu(text):
    return re.findall(r"\w+", (text or "").lower())


def _huan_luyen():
    tu_dien, dem_theo_nhom, tong_theo_nhom = set(), {}, {}
    for nhom, vi_du in DU_LIEU_MAM.items():
        dem = {}
        for cum in vi_du:
            for tu in _tach_tu(cum):
                dem[tu] = dem.get(tu, 0) + 1
                tu_dien.add(tu)
        dem_theo_nhom[nhom] = dem
        tong_theo_nhom[nhom] = sum(dem.values())
    return tu_dien, dem_theo_nhom, tong_theo_nhom


_TU_DIEN, _DEM, _TONG = _huan_luyen()


def du_doan_loai(text):
    V = len(_TU_DIEN) or 1
    tokens = _tach_tu(text)
    so_nhom = len(DU_LIEU_MAM)
    diem_log = {}
    for nhom in DU_LIEU_MAM:
        s = math.log(1.0 / so_nhom)
        dem, tong = _DEM[nhom], _TONG[nhom]
        for tu in tokens:
            s += math.log((dem.get(tu, 0) + 1) / (tong + V))
        diem_log[nhom] = s
    max_log = max(diem_log.values())
    mu = {k: math.exp(v - max_log) for k, v in diem_log.items()}
    tong_mu = sum(mu.values()) or 1.0
    nhom_tot = max(mu, key=mu.get)
    return nhom_tot, mu[nhom_tot] / tong_mu, SO_KY_GOI_Y.get(nhom_tot, 36)
