# -*- coding: utf-8 -*-
from odoo import models, fields


class AssetAllocation(models.Model):
    _name = 'asset.allocation'
    _description = 'Phiếu cấp phát / bàn giao tài sản'
    _order = 'date desc, id desc'

    asset_id = fields.Many2one('asset.asset', string='Tài sản', required=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên nhận', required=True)
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban',
        related='employee_id.department_id', store=True)
    date = fields.Date(string='Ngày cấp phát', default=fields.Date.context_today, required=True)
    return_date = fields.Date(string='Ngày thu hồi')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('allocated', 'Đang sử dụng'),
        ('returned', 'Đã thu hồi'),
    ], default='draft', string='Trạng thái')
    note = fields.Text(string='Ghi chú')

    def action_allocate(self):
        for rec in self:
            rec.state = 'allocated'
            rec.asset_id.write({
                'employee_id': rec.employee_id.id,
                'department_id': rec.department_id.id,
            })

    def action_return(self):
        for rec in self:
            rec.state = 'returned'
            rec.return_date = fields.Date.context_today(self)
            rec.asset_id.write({'employee_id': False})
