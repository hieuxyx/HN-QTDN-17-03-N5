# -*- coding: utf-8 -*-
from datetime import date

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'ten asc'

    ma_dinh_danh = fields.Char("Mã định danh", required=True)
    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)

    ngay_sinh = fields.Date("Ngày sinh")
    que_quan = fields.Char("Quê quán")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    anh = fields.Binary("Ảnh")

    # --- Bổ sung để hoàn thiện HRM & phục vụ tích hợp (đề tài Quản lý tài sản) ---
    don_vi_id = fields.Many2one("don_vi", string="Đơn vị / Phòng ban")
    chuc_vu_id = fields.Many2one("chuc_vu", string="Chức vụ")
    trang_thai = fields.Selection([
        ('dang_lam', 'Đang làm việc'),
        ('nghi_viec', 'Đã nghỉ việc'),
    ], string="Trạng thái", default='dang_lam')

    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac", inverse_name="nhan_vien_id",
        string="Danh sách lịch sử công tác")
    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap", inverse_name="nhan_vien_id",
        string="Danh sách chứng chỉ bằng cấp")

    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    so_nguoi_bang_tuoi = fields.Integer(
        "Số người bằng tuổi", compute="_compute_so_nguoi_bang_tuoi", store=True)

    _sql_constraints = [
        ('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã định danh phải là duy nhất'),
    ]

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            record.ho_va_ten = ((record.ho_ten_dem or '') + ' ' + (record.ten or '')).strip()

    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        for record in self:
            record.tuoi = (date.today().year - record.ngay_sinh.year) if record.ngay_sinh else 0

    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            count = 0
            if record.tuoi and isinstance(record.id, int):
                count = self.env['nhan_vien'].search_count([
                    ('tuoi', '=', record.tuoi),
                    ('id', '!=', record.id),
                ])
            record.so_nguoi_bang_tuoi = count

    @api.onchange("ten", "ho_ten_dem")
    def _default_ma_dinh_danh(self):
        if self.ho_ten_dem and self.ten:
            chu_cai_dau = ''.join([tu[0] for tu in self.ho_ten_dem.lower().split()])
            self.ma_dinh_danh = self.ten.lower() + chu_cai_dau

    @api.constrains('ngay_sinh', 'tuoi')
    def _check_tuoi(self):
        for record in self:
            if record.ngay_sinh and record.tuoi < 18:
                raise ValidationError("Tuổi không được bé hơn 18")
