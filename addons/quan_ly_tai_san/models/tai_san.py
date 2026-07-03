# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import UserError

from .ai_goi_y import du_doan_loai, MA_NHOM
from .telegram_api import gui_tin_telegram


class TaiSan(models.Model):
    _name = 'tai_san'
    _description = 'Tài sản'
    _rec_name = 'ten_tai_san'
    _order = 'ma_tai_san'

    ma_tai_san = fields.Char("Mã tài sản", required=True, copy=False)
    ten_tai_san = fields.Char("Tên tài sản", required=True)
    mo_ta = fields.Text("Mô tả")
    loai_tai_san_id = fields.Many2one("loai_tai_san", string="Loại tài sản")
    nguoi_quan_ly_id = fields.Many2one("nhan_vien", string="Người quản lý", required=True)
    don_vi_id = fields.Many2one("don_vi", string="Đơn vị sử dụng")
    ngay_su_dung = fields.Date("Ngày đưa vào sử dụng", default=fields.Date.context_today)
    nguyen_gia = fields.Float("Nguyên giá", required=True)
    gia_tri_thu_hoi = fields.Float("Giá trị thu hồi", default=0.0)
    so_ky_khau_hao = fields.Integer("Số kỳ khấu hao (tháng)", default=12)
    phuong_phap = fields.Selection([('duong_thang', 'Đường thẳng')],
                                   string="Phương pháp khấu hao", default='duong_thang')
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('dang_su_dung', 'Đang sử dụng'),
        ('da_khau_hao_het', 'Đã khấu hao hết'),
        ('thanh_ly', 'Thanh lý'),
    ], string="Trạng thái", default='nhap')
    khau_hao_ids = fields.One2many("khau_hao_tai_san", "tai_san_id", string="Bảng khấu hao")
    gia_tri_da_khau_hao = fields.Float("Giá trị đã khấu hao", compute="_compute_gia_tri", store=True)
    gia_tri_con_lai = fields.Float("Giá trị còn lại", compute="_compute_gia_tri", store=True)

    _sql_constraints = [('ma_tai_san_unique', 'unique(ma_tai_san)', 'Mã tài sản phải là duy nhất')]

    @api.depends("nguyen_gia", "khau_hao_ids.so_tien", "khau_hao_ids.trang_thai")
    def _compute_gia_tri(self):
        for r in self:
            da_kh = sum(r.khau_hao_ids.filtered(
                lambda l: l.trang_thai == 'da_ghi_so').mapped('so_tien'))
            r.gia_tri_da_khau_hao = da_kh
            r.gia_tri_con_lai = (r.nguyen_gia or 0.0) - da_kh

    @api.onchange("loai_tai_san_id")
    def _onchange_loai_tai_san(self):
        if self.loai_tai_san_id and self.loai_tai_san_id.so_ky_mac_dinh:
            self.so_ky_khau_hao = self.loai_tai_san_id.so_ky_mac_dinh

    def action_tinh_khau_hao(self):
        """Sinh bảng khấu hao theo phương pháp đường thẳng (Mức 1)."""
        for r in self:
            if r.so_ky_khau_hao <= 0:
                raise UserError("Số kỳ khấu hao phải lớn hơn 0.")
            r.khau_hao_ids.unlink()
            gia_tri_kh = (r.nguyen_gia or 0.0) - (r.gia_tri_thu_hoi or 0.0)
            muc_thang = round(gia_tri_kh / r.so_ky_khau_hao)
            ngay_bd = r.ngay_su_dung or fields.Date.context_today(r)
            con_lai = r.nguyen_gia or 0.0
            dong_moi = []
            for i in range(1, r.so_ky_khau_hao + 1):
                so_tien = muc_thang if i < r.so_ky_khau_hao \
                    else gia_tri_kh - muc_thang * (r.so_ky_khau_hao - 1)
                con_lai -= so_tien
                dong_moi.append((0, 0, {
                    'ky': i,
                    'ngay': ngay_bd + relativedelta(months=i - 1),
                    'so_tien': so_tien,
                    'gia_tri_con_lai': con_lai,
                    'trang_thai': 'du_kien',
                }))
            r.khau_hao_ids = dong_moi

    def action_xac_nhan(self):
        for r in self:
            if not r.khau_hao_ids:
                r.action_tinh_khau_hao()
            r.trang_thai = 'dang_su_dung'

    def action_thanh_ly(self):
        for r in self:
            r.trang_thai = 'thanh_ly'

    # ==================== Telegram (External API) ====================
    def _thong_bao_telegram(self, noi_dung):
        ICP = self.env['ir.config_parameter'].sudo()
        token = ICP.get_param('quan_ly_tai_san.telegram_bot_token')
        chat_id = ICP.get_param('quan_ly_tai_san.telegram_chat_id')
        return gui_tin_telegram(token, chat_id, noi_dung)

    # ==================== MỨC 2: TỰ ĐỘNG GHI SỔ KHẤU HAO ====================
    def _tao_but_toan_khau_hao(self, dong):
        self.ensure_one()
        loai = self.loai_tai_san_id
        if not loai or not loai.tk_chi_phi_id or not loai.tk_hao_mon_id:
            raise UserError(
                "Loại tài sản của '%s' chưa khai báo đủ TK chi phí (642) và TK hao mòn (214)."
                % self.ten_tai_san)
        return self.env['but_toan'].create({
            'ngay': dong.ngay,
            'dien_giai': 'Khấu hao %s - kỳ %s' % (self.ten_tai_san, dong.ky),
            'nguoi_lap_id': self.nguoi_quan_ly_id.id,
            'trang_thai': 'da_ghi_so',
            'dong_but_toan_ids': [
                (0, 0, {'tai_khoan_id': loai.tk_chi_phi_id.id,
                        'dien_giai': 'Chi phí khấu hao %s' % self.ten_tai_san,
                        'ghi_no': dong.so_tien, 'ghi_co': 0.0}),
                (0, 0, {'tai_khoan_id': loai.tk_hao_mon_id.id,
                        'dien_giai': 'Hao mòn lũy kế %s' % self.ten_tai_san,
                        'ghi_no': 0.0, 'ghi_co': dong.so_tien}),
            ],
        })

    def _ghi_so_mot_dong(self, dong):
        self.ensure_one()
        but_toan = self._tao_but_toan_khau_hao(dong)
        dong.write({'but_toan_id': but_toan.id, 'trang_thai': 'da_ghi_so'})
        if self.khau_hao_ids and all(l.trang_thai == 'da_ghi_so' for l in self.khau_hao_ids):
            self.trang_thai = 'da_khau_hao_het'
            self._thong_bao_telegram(
                "✅ <b>Tài sản khấu hao hết</b>\nTài sản: %s (%s)\nNguyên giá: %s VND"
                % (self.ten_tai_san, self.ma_tai_san, '{:,.0f}'.format(self.nguyen_gia)))

    def action_ghi_so_ky_toi(self):
        for r in self:
            dong = r.khau_hao_ids.filtered(lambda l: l.trang_thai == 'du_kien').sorted('ky')[:1]
            if not dong:
                raise UserError("Tài sản '%s' đã ghi sổ hết các kỳ khấu hao." % r.ten_tai_san)
            so_tien = dong.so_tien
            ky = dong.ky
            r._ghi_so_mot_dong(dong)
            r._thong_bao_telegram(
                "🧾 Ghi sổ khấu hao kỳ %s - %s: %s VND. Giá trị còn lại: %s VND."
                % (ky, r.ten_tai_san, '{:,.0f}'.format(so_tien), '{:,.0f}'.format(r.gia_tri_con_lai)))

    def action_ghi_so_toan_bo(self):
        for r in self:
            cac_dong = r.khau_hao_ids.filtered(lambda l: l.trang_thai == 'du_kien').sorted('ky')
            so_ky = len(cac_dong)
            tong = sum(cac_dong.mapped('so_tien'))
            for dong in cac_dong:
                r._ghi_so_mot_dong(dong)
            if so_ky:
                r._thong_bao_telegram(
                    "🧾 <b>Ghi sổ toàn bộ khấu hao</b>\nTài sản: %s\nSố kỳ: %s | Tổng: %s VND"
                    % (r.ten_tai_san, so_ky, '{:,.0f}'.format(tong)))

    @api.model
    def cron_ghi_so_khau_hao(self):
        hom_nay = fields.Date.context_today(self)
        tong_ky, tong_tien, so_ts = 0, 0.0, 0
        for r in self.search([('trang_thai', '=', 'dang_su_dung')]):
            cac_dong = r.khau_hao_ids.filtered(
                lambda l: l.trang_thai == 'du_kien' and l.ngay and l.ngay <= hom_nay).sorted('ky')
            if cac_dong:
                so_ts += 1
            for dong in cac_dong:
                tong_ky += 1
                tong_tien += dong.so_tien
                r._ghi_so_mot_dong(dong)
        if tong_ky:
            self._thong_bao_telegram(
                "📊 <b>Chạy khấu hao tự động</b>\nĐã ghi sổ %s kỳ cho %s tài sản.\n"
                "Tổng chi phí khấu hao: %s VND." % (tong_ky, so_ts, '{:,.0f}'.format(tong_tien)))

    # ==================== MỨC 3: AI PHÂN LOẠI (offline) ====================
    def action_goi_y_loai_ai(self):
        self.ensure_one()
        van_ban = ('%s %s' % (self.ten_tai_san or '', self.mo_ta or '')).strip()
        if not van_ban:
            raise UserError("Hãy nhập Tên tài sản (hoặc Mô tả) trước khi để AI gợi ý.")
        nhom, do_tin_cay, so_ky = du_doan_loai(van_ban)
        Loai = self.env['loai_tai_san']
        loai = Loai.search([('ten', '=', nhom)], limit=1)
        if not loai:
            TK = self.env['tai_khoan_ke_toan']
            loai = Loai.create({
                'ma': MA_NHOM.get(nhom, 'AI'), 'ten': nhom, 'so_ky_mac_dinh': so_ky,
                'tk_tai_san_id': TK.search([('ma_tai_khoan', '=', '211')], limit=1).id,
                'tk_hao_mon_id': TK.search([('ma_tai_khoan', '=', '214')], limit=1).id,
                'tk_chi_phi_id': TK.search([('ma_tai_khoan', '=', '642')], limit=1).id,
            })
        self.loai_tai_san_id = loai.id
        self.so_ky_khau_hao = so_ky
        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {
                'title': 'AI phân loại tài sản',
                'message': 'Gợi ý nhóm: "%s" (độ tin cậy %.0f%%) → số kỳ khấu hao %d tháng.'
                           % (nhom, do_tin_cay * 100, so_ky),
                'type': 'success', 'sticky': False,
            },
        }


class KhauHaoTaiSan(models.Model):
    _name = 'khau_hao_tai_san'
    _description = 'Dòng khấu hao tài sản'
    _order = 'tai_san_id, ky'

    tai_san_id = fields.Many2one("tai_san", string="Tài sản", required=True, ondelete='cascade')
    ky = fields.Integer("Kỳ")
    ngay = fields.Date("Ngày khấu hao")
    so_tien = fields.Float("Số tiền khấu hao")
    gia_tri_con_lai = fields.Float("Giá trị còn lại")
    but_toan_id = fields.Many2one("but_toan", string="Bút toán", readonly=True)
    trang_thai = fields.Selection([('du_kien', 'Dự kiến'), ('da_ghi_so', 'Đã ghi sổ')],
                                  string="Trạng thái", default='du_kien')
