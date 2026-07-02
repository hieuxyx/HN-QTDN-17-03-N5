# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TaiKhoanKeToan(models.Model):
    _name = 'tai_khoan_ke_toan'
    _description = 'Tài khoản kế toán (hệ thống tài khoản)'
    _rec_name = 'ten_hien_thi'
    _order = 'ma_tai_khoan'

    ma_tai_khoan = fields.Char("Mã tài khoản", required=True)
    ten_tai_khoan = fields.Char("Tên tài khoản", required=True)
    ten_hien_thi = fields.Char("Hiển thị", compute="_compute_ten_hien_thi", store=True)
    loai = fields.Selection([
        ('tai_san', 'Tài sản'),
        ('no_phai_tra', 'Nợ phải trả'),
        ('von_chu_so_huu', 'Vốn chủ sở hữu'),
        ('doanh_thu', 'Doanh thu'),
        ('chi_phi', 'Chi phí'),
    ], string="Loại tài khoản", required=True, default='tai_san')

    _sql_constraints = [
        ('ma_tai_khoan_unique', 'unique(ma_tai_khoan)', 'Mã tài khoản phải là duy nhất'),
    ]

    @api.depends("ma_tai_khoan", "ten_tai_khoan")
    def _compute_ten_hien_thi(self):
        for r in self:
            r.ten_hien_thi = (r.ma_tai_khoan or '') + ' - ' + (r.ten_tai_khoan or '')
