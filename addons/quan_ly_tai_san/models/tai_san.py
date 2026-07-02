# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import UserError


class TaiSan(models.Model):
    _name = 'tai_san'
    _description = 'Tài sản'
    _rec_name = 'ten_tai_san'
    _order = 'ma_tai_san'

    ma_tai_san = fields.Char("Mã tài sản", required=True, copy=False)
    ten_tai_san = fields.Char("Tên tài sản", required=True)
    loai_tai_san_id = fields.Many2one("loai_tai_san", string="Loại tài sản")
    nguoi_quan_ly_id = fields.Many2one("nhan_vien", string="Người quản lý", required=True)
    don_vi_id = fields.Many2one("don_vi", string="Đơn vị sử dụng")
    ngay_su_dung = fields.Date("Ngày đưa vào sử dụng", default=fields.Date.context_today)
    nguyen_gia = fields.Float("Nguyên giá", required=True)
    gia_tri_thu_hoi = fields.Float("Giá trị thu hồi", default=0.0)
    so_ky_khau_hao = fields.Integer("Số kỳ khấu hao (tháng)", default=12)
    phuong_phap = fields.Selection([
        ('duong_thang', 'Đường thẳng'),
    ], string="Phương pháp khấu hao", default='duong_thang')
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('dang_su_dung', 'Đang sử dụng'),
        ('da_khau_hao_het', 'Đã khấu hao hết'),
        ('thanh_ly', 'Thanh lý'),
    ], string="Trạng thái", default='nhap')
    khau_hao_ids = fields.One2many("khau_hao_tai_san", "tai_san_id", string="Bảng khấu hao")
    gia_tri_da_khau_hao = fields.Float("Giá trị đã khấu hao", compute="_compute_gia_tri", store=True)
    gia_tri_con_lai = fields.Float("Giá trị còn lại", compute="_compute_gia_tri", store=True)

    _sql_constraints = [
        ('ma_tai_san_unique', 'unique(ma_tai_san)', 'Mã tài sản phải là duy nhất'),
    ]

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
        """Sinh bảng khấu hao theo phương pháp đường thẳng (Mức 1: bấm nút)."""
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

    # ==================== MỨC 2: TỰ ĐỘNG GHI SỔ KHẤU HAO ====================
    def _tao_but_toan_khau_hao(self, dong):
        """Tạo bút toán Nợ 642 / Có 214 cho một kỳ khấu hao (sang module Kế toán)."""
        self.ensure_one()
        loai = self.loai_tai_san_id
        if not loai or not loai.tk_chi_phi_id or not loai.tk_hao_mon_id:
            raise UserError(
                "Loại tài sản của '%s' chưa khai báo đủ TK chi phí (642) và TK hao mòn (214)."
                % self.ten_tai_san)
        but_toan = self.env['but_toan'].create({
            'ngay': dong.ngay,
            'dien_giai': 'Khấu hao %s - kỳ %s' % (self.ten_tai_san, dong.ky),
            'nguoi_lap_id': self.nguoi_quan_ly_id.id,
            'trang_thai': 'da_ghi_so',
            'dong_but_toan_ids': [
                (0, 0, {
                    'tai_khoan_id': loai.tk_chi_phi_id.id,
                    'dien_giai': 'Chi phí khấu hao %s' % self.ten_tai_san,
                    'ghi_no': dong.so_tien,
                    'ghi_co': 0.0,
                }),
                (0, 0, {
                    'tai_khoan_id': loai.tk_hao_mon_id.id,
                    'dien_giai': 'Hao mòn lũy kế %s' % self.ten_tai_san,
                    'ghi_no': 0.0,
                    'ghi_co': dong.so_tien,
                }),
            ],
        })
        return but_toan

    def _ghi_so_mot_dong(self, dong):
        self.ensure_one()
        but_toan = self._tao_but_toan_khau_hao(dong)
        dong.write({'but_toan_id': but_toan.id, 'trang_thai': 'da_ghi_so'})
        if self.khau_hao_ids and all(l.trang_thai == 'da_ghi_so' for l in self.khau_hao_ids):
            self.trang_thai = 'da_khau_hao_het'

    def action_ghi_so_ky_toi(self):
        """Ghi sổ kỳ khấu hao gần nhất chưa ghi (mỗi lần bấm = 1 kỳ)."""
        for r in self:
            dong = r.khau_hao_ids.filtered(
                lambda l: l.trang_thai == 'du_kien').sorted('ky')[:1]
            if not dong:
                raise UserError("Tài sản '%s' đã ghi sổ hết các kỳ khấu hao." % r.ten_tai_san)
            r._ghi_so_mot_dong(dong)

    def action_ghi_so_toan_bo(self):
        """Ghi sổ toàn bộ các kỳ còn lại (tiện demo nhanh)."""
        for r in self:
            for dong in r.khau_hao_ids.filtered(
                    lambda l: l.trang_thai == 'du_kien').sorted('ky'):
                r._ghi_so_mot_dong(dong)

    @api.model
    def cron_ghi_so_khau_hao(self):
        """Tác vụ định kỳ: tự ghi sổ các kỳ khấu hao đã đến hạn cho mọi tài sản đang dùng."""
        hom_nay = fields.Date.context_today(self)
        for r in self.search([('trang_thai', '=', 'dang_su_dung')]):
            for dong in r.khau_hao_ids.filtered(
                    lambda l: l.trang_thai == 'du_kien' and l.ngay and l.ngay <= hom_nay
            ).sorted('ky'):
                r._ghi_so_mot_dong(dong)


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
    trang_thai = fields.Selection([
        ('du_kien', 'Dự kiến'),
        ('da_ghi_so', 'Đã ghi sổ'),
    ], string="Trạng thái", default='du_kien')
