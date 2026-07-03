# -*- coding: utf-8 -*-
from odoo import models, fields


class LoaiTaiSan(models.Model):
    _name = 'loai_tai_san'
    _description = 'Loại tài sản'
    _rec_name = 'ten'
    _order = 'ma'

    ma = fields.Char("Mã loại", required=True)
    ten = fields.Char("Tên loại", required=True)
    so_ky_mac_dinh = fields.Integer("Số kỳ khấu hao mặc định (tháng)", default=12)
    tk_tai_san_id = fields.Many2one("tai_khoan_ke_toan", string="TK tài sản (211)")
    tk_hao_mon_id = fields.Many2one("tai_khoan_ke_toan", string="TK hao mòn (214)")
    tk_chi_phi_id = fields.Many2one("tai_khoan_ke_toan", string="TK chi phí khấu hao (642)")

    _sql_constraints = [('ma_unique', 'unique(ma)', 'Mã loại tài sản phải là duy nhất')]
