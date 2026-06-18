# -*- coding: utf-8 -*-
from odoo import models, fields


class AssetCategory(models.Model):
    _name = 'asset.category'
    _description = 'Nhóm tài sản cố định'

    name = fields.Char(string='Tên nhóm', required=True)
    code = fields.Char(string='Mã nhóm')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        default=lambda self: self.env.company)

    # --- Tham số khấu hao mặc định cho cả nhóm ---
    method = fields.Selection([
        ('linear', 'Đường thẳng'),
        ('degressive', 'Số dư giảm dần'),
    ], string='Phương pháp khấu hao', default='linear', required=True)
    method_number = fields.Integer(
        string='Số kỳ khấu hao', default=60,
        help='Tổng số kỳ (tháng) trích khấu hao.')
    method_period = fields.Integer(
        string='Số tháng mỗi kỳ', default=1,
        help='Khoảng cách giữa hai lần ghi khấu hao, tính theo tháng.')
    degressive_factor = fields.Float(
        string='Hệ số giảm dần', default=2.0,
        help='Chỉ áp dụng với phương pháp số dư giảm dần.')
    prorata = fields.Boolean(
        string='Khấu hao theo ngày (prorata)',
        help='Tính khấu hao từ đúng ngày đưa vào sử dụng thay vì đầu kỳ.')

    # --- Tài khoản kế toán mặc định (VAS) ---
    account_asset_id = fields.Many2one(
        'account.account', string='TK tài sản (211/213)',
        domain="[('company_id', '=', company_id)]")
    account_depreciation_id = fields.Many2one(
        'account.account', string='TK hao mòn lũy kế (214)',
        domain="[('company_id', '=', company_id)]")
    account_expense_id = fields.Many2one(
        'account.account', string='TK chi phí khấu hao (627/641/642)',
        domain="[('company_id', '=', company_id)]")
    journal_id = fields.Many2one(
        'account.journal', string='Sổ nhật ký',
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]")
