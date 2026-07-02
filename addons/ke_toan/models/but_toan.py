# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ButToan(models.Model):
    _name = 'but_toan'
    _description = 'Bút toán (chứng từ ghi sổ)'
    _rec_name = 'so_but_toan'
    _order = 'ngay desc, so_but_toan desc'

    so_but_toan = fields.Char("Số bút toán", required=True, copy=False,
                              default=lambda self: self._so_but_toan_moi())
    ngay = fields.Date("Ngày ghi sổ", required=True, default=fields.Date.context_today)
    dien_giai = fields.Char("Diễn giải")
    nguoi_lap_id = fields.Many2one("nhan_vien", string="Người lập")
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('da_ghi_so', 'Đã ghi sổ'),
    ], string="Trạng thái", default='nhap')
    dong_but_toan_ids = fields.One2many("dong_but_toan", "but_toan_id", string="Các dòng bút toán")
    tong_no = fields.Float("Tổng Nợ", compute="_compute_tong", store=True)
    tong_co = fields.Float("Tổng Có", compute="_compute_tong", store=True)

    @api.model
    def _so_but_toan_moi(self):
        return self.env['ir.sequence'].next_by_code('but_toan.sequence') or 'BT/MOI'

    @api.depends("dong_but_toan_ids.ghi_no", "dong_but_toan_ids.ghi_co")
    def _compute_tong(self):
        for r in self:
            r.tong_no = sum(r.dong_but_toan_ids.mapped('ghi_no'))
            r.tong_co = sum(r.dong_but_toan_ids.mapped('ghi_co'))

    def action_ghi_so(self):
        for r in self:
            r.trang_thai = 'da_ghi_so'

    def action_ve_nhap(self):
        for r in self:
            r.trang_thai = 'nhap'


class DongButToan(models.Model):
    _name = 'dong_but_toan'
    _description = 'Dòng bút toán'
    _order = 'but_toan_id'

    but_toan_id = fields.Many2one("but_toan", string="Bút toán", required=True, ondelete='cascade')
    tai_khoan_id = fields.Many2one("tai_khoan_ke_toan", string="Tài khoản", required=True)
    dien_giai = fields.Char("Diễn giải")
    ghi_no = fields.Float("Ghi Nợ")
    ghi_co = fields.Float("Ghi Có")
    ngay = fields.Date("Ngày", related='but_toan_id.ngay', store=True)
