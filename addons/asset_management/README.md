# Module Quản lý tài sản & Khấu hao (Odoo 15)

Module quản lý tài sản cố định (TSCĐ), **tự động trích khấu hao hàng tháng và ghi vào sổ cái**,
tích hợp với **Nhân sự** (cấp phát, bàn giao) và **Kế toán** (bút toán, sổ cái).

## Phụ thuộc
`base`, `mail`, `hr`, `account` — cài được trên Odoo 15 Community.

## Cài đặt
1. Copy thư mục `asset_management/` vào thư mục addons của Odoo.
2. Khởi động lại Odoo với `-u all` hoặc bật chế độ Developer.
3. Vào **Apps → Update Apps List**, tìm "Quản lý tài sản" và cài đặt.
4. Cấp quyền cho người dùng: **Settings → Users → nhóm "Quản lý tài sản"**.

## Cấu hình nhanh
1. Vào **Quản lý tài sản → Cấu hình → Nhóm tài sản**, tạo nhóm và chọn:
   - TK tài sản (211), TK hao mòn (214), TK chi phí (627/641/642), Sổ nhật ký (loại "Khác/General").
2. Tạo tài sản, chọn nhóm → tham số & tài khoản tự điền.
3. Bấm **Đưa vào sử dụng** → hệ thống sinh bảng khấu hao.
4. Cron "Ghi sổ khấu hao định kỳ" chạy hằng tháng; có thể bấm **Ghi sổ** thủ công trên từng dòng để demo.

## Các model chính
| Model | Vai trò |
|---|---|
| `asset.category` | Nhóm tài sản, tham số & tài khoản mặc định |
| `asset.asset` | Hồ sơ TSCĐ, logic sinh bảng khấu hao, thanh lý |
| `asset.depreciation.line` | Dòng khấu hao từng kỳ + bút toán |
| `asset.allocation` | Phiếu cấp phát / bàn giao cho nhân viên |
| `hr.employee` (kế thừa) | Gắn tài sản với nhân viên, chặn nghỉ việc khi còn tài sản |

## Điểm tích hợp 3 module
- **Tài sản ↔ Nhân sự:** `employee_id`, `department_id` trên tài sản; chặn lưu trữ nhân viên còn giữ tài sản.
- **Tài sản ↔ Kế toán:** cron sinh `account.move` (Nợ 627/641/642 / Có 214); thanh lý ghi giảm.
- **Nhân sự ↔ Kế toán:** bộ phận sử dụng (HR) quyết định TK chi phí khấu hao ghi vào (641/642/627).
