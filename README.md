# Hệ thống ERP mini — Đề tài 5: Quản lý Tài sản + Kế toán + HRM

Bài tập lớn học phần **Thực tập Doanh nghiệp / Hội nhập và Quản trị Phần mềm Doanh nghiệp** — Khoa CNTT, Đại học Đại Nam (FIT-DNU).
Phát triển trên nền tảng **Odoo 15 (Python)**, kế thừa và mở rộng từ kho mã nguồn của Khoa.

> **Đề tài 5:** Kết hợp *Quản lý tài sản* + *Quản lý Tài chính/Kế toán* + *Quản lý nhân sự (HRM)* — tự động tính khấu hao tài sản hằng tháng, ghi nhận vào sổ cái kế toán, hỗ trợ quản lý dòng tiền và ngân sách mua sắm.

---

## 1. Thông tin nhóm

- **Nhóm:** 05 — Lớp HN-QTDN-17-03
- **Repo:** https://github.com/hieuxyx/HN-QTDN-17-03-N5

| STT | Họ và tên | MSSV | Phân công chính |
|-----|-----------|------|-----------------|
| 1 | Vi Đình Hiếu | 1771020265 |  |
| 2 | Ngô Văn huy | 〉 |  |
| 3 | Ngô Đặng Tuấn Anh |  |  |
| 4 | Lục Đức Lương | |  |

> Gợi ý phân công để thể hiện rõ đóng góp: *module HRM & tích hợp*, *module Kế toán & sổ cái*, *module Tài sản & khấu hao/tự động hóa*, *tính năng AI (OCR/Chatbot) & Telegram*, *sơ đồ nghiệp vụ & tài liệu*.

---

## 2. Kiến trúc hệ thống

Hệ thống gồm **03 module tách riêng nhưng liên kết dữ liệu**, trong đó HRM là dữ liệu gốc về nhân viên:

| Module | Vai trò | Model chính |
|--------|---------|-------------|
| `nhan_su` (HRM) | Dữ liệu gốc: nhân viên, phòng ban, chức vụ | `nhan_vien`, `don_vi`, `chuc_vu` |
| `ke_toan` | Hệ thống tài khoản, bút toán, sổ cái | `tai_khoan_ke_toan`, `but_toan`, `dong_but_toan` |
| `quan_ly_tai_san` | Loại tài sản, tài sản, bảng khấu hao | `loai_tai_san`, `tai_san`, `khau_hao_tai_san` |

**Thứ tự phụ thuộc:** `nhan_su` → `ke_toan` → `quan_ly_tai_san`.

Sơ đồ luồng nghiệp vụ end-to-end: xem [`docs/business-flow/`](docs/business-flow/).

---

## 3. Chức năng theo mức độ hoàn thiện

### Mức 1 — Tích hợp dữ liệu
- Đủ 03 module, mỗi module có model, menu, form/list view và dữ liệu riêng.
- HRM là nguồn nhân viên: tài sản và bút toán **chọn nhân viên từ HRM**, không nhập lại thủ công.
- Quan hệ dữ liệu rõ ràng (Many2one/One2many) giữa các module.

### Mức 2 — Tự động hóa quy trình
- Nút **"Ghi sổ khấu hao"** (từng kỳ / toàn bộ) và **tác vụ định kỳ (cron)** hằng tháng.
- Khi ghi sổ, hệ thống **tự động tạo bút toán Nợ 642 / Có 214** trong module Kế toán, người lập lấy từ HRM, cập nhật dòng khấu hao và giảm giá trị còn lại.
- Luồng đi qua đủ 03 module: **HRM → Tài sản → Kế toán**.

### Mức 3 — AI & External API
- **OCR hóa đơn (Gemini):** upload ảnh hóa đơn → bóc tách Tên/Nguyên giá/Ngày → tạo sẵn phiếu tài sản.
- **Trợ lý AI hỏi-đáp (Gemini):** hỏi bằng ngôn ngữ tự nhiên về dữ liệu tài sản (VD: "tài sản nào sắp hết khấu hao?").
- **AI phân loại tài sản (Naive Bayes, offline):** gợi ý nhóm tài sản và số kỳ khấu hao từ tên/mô tả.
- **External API — Telegram:** gửi thông báo khi ghi sổ khấu hao và khi tài sản khấu hao hết.

---

## 4. Quan hệ dữ liệu & điểm tích hợp

- `tai_san.nguoi_quan_ly_id` → `nhan_vien` ; `tai_san.don_vi_id` → `don_vi`  *(HRM → Tài sản)*
- `loai_tai_san.tk_tai_san_id / tk_hao_mon_id / tk_chi_phi_id` → `tai_khoan_ke_toan`  *(Tài sản → Kế toán)*
- `but_toan.nguoi_lap_id` → `nhan_vien`  *(HRM → Kế toán)*
- `khau_hao_tai_san.but_toan_id` → `but_toan`  *(cầu nối tự động hóa Mức 2)*

---

## 5. Công nghệ sử dụng

- **Odoo 15** (Python 3.9), PostgreSQL — chạy bằng **Docker Compose**.
- **Google Gemini API** (`gemini-2.5-flash`) cho OCR và Chatbot.
- **Telegram Bot API** cho thông báo.
- Thuật toán **Naive Bayes** (thuần Python) cho phân loại tài sản offline.

---

## 6. Cài đặt & chạy

```bash
# 1. Bật Postgres + Odoo bằng Docker
docker compose -f docker-compose-btl.yml up -d

# 2. Cài/nâng cấp 3 module (lần đầu dùng -i, cập nhật dùng -u)
docker exec btl_odoo odoo -d QuanLyTaiSan -i nhan_su,ke_toan,quan_ly_tai_san --stop-after-init
docker restart btl_odoo
```

Mở trình duyệt `http://localhost:8069`, chọn database, cài "Quản lý tài sản" (tự kéo theo 2 module còn lại).

## 7. Cấu hình AI & Telegram

Nhập vào **Thiết lập → Kỹ thuật → Tham số hệ thống** (không hardcode trong code):

| Tham số | Giá trị |
|---------|---------|
| `quan_ly_tai_san.gemini_api_key` | API key từ https://aistudio.google.com/apikey |
| `quan_ly_tai_san.gemini_model` | `gemini-2.5-flash` |
| `quan_ly_tai_san.telegram_bot_token` | token từ @BotFather |
| `quan_ly_tai_san.telegram_chat_id` | chat_id lấy qua `getUpdates` |

> Các khóa/token **không** được lưu trong mã nguồn — chỉ lưu trong cơ sở dữ liệu, nên an toàn khi đẩy lên GitHub.

## 8. Hướng dẫn sử dụng nhanh

1. **HRM:** tạo nhân viên (kèm phòng ban, chức vụ).
2. **Tài sản:** tạo tài sản, chọn người quản lý từ HRM → *Tính bảng khấu hao* → *Xác nhận*.
3. **Ghi sổ:** bấm *Ghi sổ khấu hao* → hệ thống tự tạo bút toán; kiểm tra ở **Kế toán → Sổ cái**.
4. **AI:** *Nhập từ hóa đơn (AI)* để OCR; *Trợ lý AI* để hỏi-đáp.

---

## 9. Cải tiến so với mã nguồn gốc

Module `nhan_su` được kế thừa từ kho của Khoa và đã được nhóm **audit, sửa lỗi và mở rộng**:

- Sửa lỗi trường tính toán `so_nguoi_bang_tuoi` (trỏ sai tên hàm compute) và lỗi id ảo khi tạo mới.
- Sửa lỗi chính tả `_sql_constrains` → `_sql_constraints`.
- Sửa ràng buộc tuổi (đang chặn cả nhân viên chưa nhập ngày sinh).
- Gỡ tham chiếu file demo không tồn tại trong manifest (gây lỗi cài đặt).
- **Bổ sung** liên kết `don_vi_id`, `chuc_vu_id` và trường `trang_thai` cho nhân viên.

Hai module `ke_toan` và `quan_ly_tai_san` do nhóm **phát triển mới hoàn toàn**.

---

## 10. Nguồn tham khảo & liêm chính học thuật

- Nền tảng Odoo 15 và module `nhan_su` kế thừa từ: **https://github.com/FIT-DNU/Business-Internship** (Khoa CNTT — ĐH Đại Nam).
- Theo quy định học phần (mục IV), nhóm được phép sử dụng công cụ AI Code Assistant để hỗ trợ lập trình. Nhóm đã **đọc hiểu, kiểm thử và giải thích được** toàn bộ luồng xử lý của sản phẩm.
- Lịch sử phát triển được thể hiện qua **commit theo tiến độ** trên GitHub.

---

## 11. Cấu trúc thư mục

```
addons/
├── nhan_su/            # HRM (kế thừa + cải tiến)
├── ke_toan/            # Hệ thống tài khoản, bút toán, sổ cái
└── quan_ly_tai_san/    # Loại/tài sản, khấu hao, tự động hóa, AI, Telegram
docs/
└── business-flow/      # Sơ đồ luồng nghiệp vụ (Swimlane/BPMN)
```
