# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AssetBudget(models.Model):
    _name = 'asset.budget'
    _description = 'Ngân sách mua sắm tài sản'
    _order = 'date_from desc, id desc'

    name = fields.Char(string='Tên ngân sách', required=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban', required=True)  # HR LINK
    date_from = fields.Date(string='Từ ngày', required=True)
    date_to = fields.Date(string='Đến ngày', required=True)
    planned_amount = fields.Monetary(string='Ngân sách kế hoạch', required=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đang áp dụng'),
        ('done', 'Đã đóng'),
    ], default='draft', string='Trạng thái')

    request_ids = fields.One2many('asset.purchase.request', 'budget_id', string='Đề xuất')
    committed_amount = fields.Monetary(
        string='Đã cam kết (đề xuất duyệt)', compute='_compute_amounts')
    actual_amount = fields.Monetary(
        string='Đã thực chi (đã mua)', compute='_compute_amounts')
    available_amount = fields.Monetary(
        string='Còn lại', compute='_compute_amounts')

    @api.depends('planned_amount', 'request_ids.state', 'request_ids.total_cost')
    def _compute_amounts(self):
        for b in self:
            committed = sum(b.request_ids.filtered(
                lambda r: r.state in ('approved', 'done')).mapped('total_cost'))
            actual = sum(b.request_ids.filtered(
                lambda r: r.state == 'done').mapped('total_cost'))
            b.committed_amount = committed
            b.actual_amount = actual
            b.available_amount = b.planned_amount - committed

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_close(self):
        self.write({'state': 'done'})
