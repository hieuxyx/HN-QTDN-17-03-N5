# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class AssetPurchaseRequest(models.Model):
    _name = 'asset.purchase.request'
    _description = 'Đề xuất mua sắm tài sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, id desc'

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char(string='Mã phiếu', default='New', copy=False, readonly=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Người đề xuất', required=True,
        default=lambda self: self._default_employee())  # HR
    department_id = fields.Many2one('hr.department', string='Phòng ban', required=True)  # HR
    request_date = fields.Date(string='Ngày đề xuất', default=fields.Date.context_today, required=True)
    description = fields.Char(string='Tài sản cần mua', required=True)
    category_id = fields.Many2one('asset.category', string='Nhóm tài sản', required=True)
    quantity = fields.Integer(string='Số lượng', default=1, required=True)
    unit_cost = fields.Monetary(string='Đơn giá dự kiến', required=True)
    total_cost = fields.Monetary(string='Thành tiền', compute='_compute_total', store=True)
    budget_id = fields.Many2one('asset.budget', string='Ngân sách')
    account_payable_id = fields.Many2one('account.account', string='TK đối ứng (331/112)')

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('to_approve', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('refused', 'Từ chối'),
        ('done', 'Đã mua / Ghi tăng'),
    ], default='draft', string='Trạng thái', tracking=True)
    over_budget = fields.Boolean(string='Vượt ngân sách', compute='_compute_over_budget')
    asset_id = fields.Many2one('asset.asset', string='Tài sản đã tạo', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('asset.purchase.request') or 'New'
        return super().create(vals_list)

    @api.depends('quantity', 'unit_cost')
    def _compute_total(self):
        for r in self:
            r.total_cost = r.quantity * r.unit_cost

    @api.depends('budget_id', 'budget_id.available_amount', 'total_cost')
    def _compute_over_budget(self):
        for r in self:
            r.over_budget = bool(r.budget_id) and r.total_cost > r.budget_id.available_amount

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.employee_id.department_id:
            self.department_id = self.employee_id.department_id

    # --- Quy trình ---
    def action_submit(self):
        self.write({'state': 'to_approve'})

    def action_approve(self):
        for r in self:
            if r.over_budget:
                raise UserError(
                    'Đề xuất "%s" vượt ngân sách còn lại của phòng %s. '
                    'Vui lòng điều chỉnh giá trị hoặc tăng ngân sách.'
                    % (r.name, r.department_id.name))
            r.state = 'approved'

    def action_refuse(self):
        self.write({'state': 'refused'})

    def action_reset(self):
        self.write({'state': 'draft'})

    def action_purchase(self):
        """Ghi tăng tài sản từ đề xuất đã duyệt + (tùy chọn) bút toán Nợ 211 / Có 331."""
        AssetModel = self.env['asset.asset']
        for r in self:
            if r.state != 'approved':
                raise UserError('Chỉ ghi tăng tài sản từ đề xuất đã được duyệt.')
            cat = r.category_id
            asset = AssetModel.create({
                'name': r.description,
                'category_id': cat.id,
                'original_value': r.total_cost,
                'acquisition_date': fields.Date.context_today(self),
                'date_start': fields.Date.context_today(self),
                'department_id': r.department_id.id,
                'method': cat.method,
                'method_number': cat.method_number,
                'method_period': cat.method_period,
                'degressive_factor': cat.degressive_factor,
                'prorata': cat.prorata,
                'account_asset_id': cat.account_asset_id.id,
                'account_depreciation_id': cat.account_depreciation_id.id,
                'account_expense_id': cat.account_expense_id.id,
                'journal_id': cat.journal_id.id,
            })
            # Bút toán ghi tăng (tùy chọn nếu đã cấu hình tài khoản)
            journal = cat.journal_id
            if cat.account_asset_id and r.account_payable_id and journal:
                move = self.env['account.move'].create({
                    'journal_id': journal.id,
                    'date': fields.Date.context_today(self),
                    'ref': 'Ghi tăng TS: %s' % r.name,
                    'move_type': 'entry',
                    'line_ids': [
                        (0, 0, {'name': r.description, 'account_id': cat.account_asset_id.id,
                                'debit': r.total_cost, 'credit': 0.0}),
                        (0, 0, {'name': r.description, 'account_id': r.account_payable_id.id,
                                'debit': 0.0, 'credit': r.total_cost}),
                    ],
                })
                move.action_post()
            r.asset_id = asset.id
            r.state = 'done'
        return True

    def action_view_asset(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'asset.asset',
            'res_id': self.asset_id.id,
            'view_mode': 'form',
        }
