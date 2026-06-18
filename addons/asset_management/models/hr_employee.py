# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    asset_ids = fields.One2many('asset.asset', 'employee_id', string='Tài sản quản lý')
    asset_count = fields.Integer(string='Số tài sản', compute='_compute_asset_count')

    @api.depends('asset_ids', 'asset_ids.state')
    def _compute_asset_count(self):
        for emp in self:
            emp.asset_count = len(emp.asset_ids.filtered(lambda a: a.state != 'disposed'))

    def action_view_employee_assets(self):
        self.ensure_one()
        return {
            'name': 'Tài sản của %s' % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'asset.asset',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def write(self, vals):
        # NGHIỆP VỤ LIÊN KẾT HR <-> TÀI SẢN:
        # Không cho lưu trữ (cho nghỉ) nhân viên khi còn tài sản chưa bàn giao.
        if vals.get('active') is False:
            for emp in self:
                pending = emp.asset_ids.filtered(lambda a: a.state in ('draft', 'open', 'paused'))
                if pending:
                    raise UserError(
                        'Nhân viên %s còn %d tài sản chưa bàn giao. '
                        'Vui lòng thu hồi/điều chuyển trước khi cho nghỉ việc.'
                        % (emp.name, len(pending)))
        return super().write(vals)
