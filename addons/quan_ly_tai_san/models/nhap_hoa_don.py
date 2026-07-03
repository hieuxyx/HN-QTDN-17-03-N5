# -*- coding: utf-8 -*-
import json
import re

from odoo import models, fields
from odoo.exceptions import UserError

from .gemini_api import goi_gemini


class NhapHoaDonAI(models.TransientModel):
    _name = 'nhap_hoa_don_ai'
    _description = 'Nhập tài sản từ hóa đơn (OCR AI)'

    hoa_don = fields.Binary("Ảnh hóa đơn", required=True)
    ten_file = fields.Char("Tên file")

    def action_ocr(self):
        self.ensure_one()
        if not self.hoa_don:
            raise UserError("Hãy tải lên ảnh hóa đơn trước.")
        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('quan_ly_tai_san.gemini_api_key')
        model = ICP.get_param('quan_ly_tai_san.gemini_model') or 'gemini-2.5-flash'
        if not api_key:
            raise UserError("Chưa cấu hình Gemini API key ở Tham số hệ thống "
                            "(quan_ly_tai_san.gemini_api_key).")
        prompt = (
            "Đây là ảnh hóa đơn/biên nhận mua tài sản. Đọc và trả về JSON đúng cấu trúc:\n"
            '{"ten": "tên tài sản", "nguyen_gia": so_tien_VND_dang_so, "ngay_mua": "YYYY-MM-DD"}\n'
            "Nếu không thấy trường nào thì để rỗng hoặc 0. Chỉ trả JSON."
        )
        b64 = self.hoa_don.decode() if isinstance(self.hoa_don, bytes) else self.hoa_don
        mime = 'image/png' if (self.ten_file or '').lower().endswith('.png') else 'image/jpeg'
        van_ban = goi_gemini(api_key, model, prompt, anh_base64=b64, anh_mime=mime, json_output=True)
        v = van_ban.strip()
        if v.startswith('```'):
            v = re.sub(r'^```[a-zA-Z]*', '', v).rsplit('```', 1)[0].strip()
        try:
            dl = json.loads(v)
        except Exception:
            raise UserError("AI trả về không phải JSON hợp lệ:\n%s" % van_ban[:300])
        ten = (dl.get('ten') or '').strip()
        ngay = str(dl.get('ngay_mua') or '').strip()
        gia_raw = dl.get('nguyen_gia') or 0
        if isinstance(gia_raw, str):
            so = re.sub(r'[^0-9]', '', gia_raw)
            gia = float(so) if so else 0.0
        else:
            gia = float(gia_raw or 0)
        ctx = {
            'default_ten_tai_san': ten or 'Tài sản từ hóa đơn',
            'default_nguyen_gia': gia,
            'default_mo_ta': 'Tạo tự động từ hóa đơn bằng OCR AI.',
        }
        if re.match(r'^\d{4}-\d{2}-\d{2}$', ngay):
            ctx['default_ngay_su_dung'] = ngay
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tài sản (từ hóa đơn)',
            'res_model': 'tai_san',
            'view_mode': 'form',
            'target': 'current',
            'context': ctx,
        }
