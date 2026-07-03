# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import UserError

from .gemini_api import goi_gemini


class TroLyTaiSan(models.TransientModel):
    _name = 'tro_ly_tai_san'
    _description = 'Trợ lý AI hỏi - đáp tài sản'

    cau_hoi = fields.Text("Câu hỏi", required=True)
    tra_loi = fields.Text("Trả lời", readonly=True)

    def _du_lieu_tai_san(self):
        dong = []
        for ts in self.env['tai_san'].search([], limit=200):
            con_lai_ky = len(ts.khau_hao_ids.filtered(lambda l: l.trang_thai == 'du_kien'))
            dong.append(
                "- %s | loại: %s | nguyên giá: %.0f | còn lại: %.0f | trạng thái: %s | "
                "quản lý: %s | kỳ chưa ghi: %d"
                % (ts.ten_tai_san, ts.loai_tai_san_id.ten or '', ts.nguyen_gia,
                   ts.gia_tri_con_lai, ts.trang_thai, ts.nguoi_quan_ly_id.ho_va_ten or '', con_lai_ky))
        return "\n".join(dong) or "(chưa có tài sản)"

    def action_hoi(self):
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('quan_ly_tai_san.gemini_api_key')
        model = ICP.get_param('quan_ly_tai_san.gemini_model') or 'gemini-2.5-flash'
        if not api_key:
            raise UserError("Chưa cấu hình Gemini API key ở Tham số hệ thống "
                            "(quan_ly_tai_san.gemini_api_key).")
        prompt = (
            "Bạn là trợ lý quản lý tài sản của công ty. Danh sách tài sản hiện có:\n%s\n\n"
            "Chỉ dựa trên dữ liệu trên, trả lời ngắn gọn bằng tiếng Việt. "
            "Nếu dữ liệu không đủ, hãy nói rõ.\n\nCâu hỏi: %s"
            % (self._du_lieu_tai_san(), self.cau_hoi)
        )
        self.tra_loi = goi_gemini(api_key, model, prompt)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trợ lý AI tài sản',
            'res_model': 'tro_ly_tai_san',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
