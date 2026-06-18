# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class AssetDepreciationLine(models.Model):
    _name = 'asset.depreciation.line'
    _description = 'Dòng khấu hao tài sản'
    _order = 'depreciation_date, sequence, id'

    asset_id = fields.Many2one('asset.asset', string='Tài sản', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='asset_id.company_id', store=True)
    currency_id = fields.Many2one(related='asset_id.currency_id', store=True)

    sequence = fields.Integer(string='Kỳ', default=1)
    name = fields.Char(string='Tên kỳ')
    amount = fields.Monetary(string='Mức khấu hao')
    depreciated_value = fields.Monetary(string='Lũy kế đã khấu hao')
    remaining_value = fields.Monetary(string='Còn phải khấu hao')
    depreciation_date = fields.Date(string='Ngày ghi khấu hao')
    move_id = fields.Many2one('account.move', string='Bút toán', readonly=True, ondelete='set null')
    move_posted = fields.Boolean(string='Đã ghi sổ', compute='_compute_move_posted', store=True)

    @api.depends('move_id')
    def _compute_move_posted(self):
        for line in self:
            line.move_posted = bool(line.move_id)

    def _create_moves(self):
        """Tạo & ghi sổ bút toán khấu hao cho các dòng đang chọn.
        Định khoản: Nợ 627/641/642 (chi phí) / Có 214 (hao mòn lũy kế).
        Tài khoản chi phí lấy theo bộ phận sử dụng -> điểm nối HR + Kế toán.
        """
        moves = self.env['account.move']
        for line in self:
            if line.move_id:
                continue
            asset = line.asset_id
            journal = asset.journal_id or asset.category_id.journal_id
            if not (asset.account_expense_id and asset.account_depreciation_id and journal):
                raise UserError(
                    'Tài sản %s chưa cấu hình đủ tài khoản/sổ nhật ký để ghi khấu hao.' % asset.name)
            move = self.env['account.move'].create({
                'journal_id': journal.id,
                'date': line.depreciation_date,
                'ref': '%s - khấu hao %s' % (asset.name, line.name or ''),
                'move_type': 'entry',
                'line_ids': [
                    (0, 0, {
                        'name': 'Khấu hao %s' % asset.name,
                        'account_id': asset.account_expense_id.id,
                        'debit': line.amount, 'credit': 0.0,
                    }),
                    (0, 0, {
                        'name': 'Khấu hao %s' % asset.name,
                        'account_id': asset.account_depreciation_id.id,
                        'debit': 0.0, 'credit': line.amount,
                    }),
                ],
            })
            move.action_post()
            line.move_id = move.id
            moves += move
        return moves

    def action_create_move(self):
        """Nút ghi sổ thủ công cho một dòng (dùng khi không chờ cron)."""
        self._create_moves()
        return True
