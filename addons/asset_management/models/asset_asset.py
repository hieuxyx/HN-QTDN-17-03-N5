# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class AssetAsset(models.Model):
    _name = 'asset.asset'
    _description = 'Tài sản cố định'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'acquisition_date desc, id desc'

    name = fields.Char(string='Tên tài sản', required=True, tracking=True)
    code = fields.Char(string='Mã tài sản')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', store=True)

    category_id = fields.Many2one(
        'asset.category', string='Nhóm tài sản', required=True, tracking=True)

    # --- Giá trị ---
    original_value = fields.Monetary(string='Nguyên giá', tracking=True)
    salvage_value = fields.Monetary(string='Giá trị thanh lý ước tính', default=0.0)
    depreciated_value = fields.Monetary(
        string='Đã khấu hao lũy kế', compute='_compute_values', store=True)
    value_residual = fields.Monetary(
        string='Giá trị còn lại', compute='_compute_values', store=True)

    # --- Thời gian ---
    acquisition_date = fields.Date(
        string='Ngày mua', default=fields.Date.context_today, required=True)
    date_start = fields.Date(
        string='Ngày bắt đầu khấu hao', required=True,
        default=fields.Date.context_today)

    # --- Tham số khấu hao (mặc định lấy từ nhóm, cho phép sửa) ---
    method = fields.Selection([
        ('linear', 'Đường thẳng'),
        ('degressive', 'Số dư giảm dần'),
    ], string='Phương pháp', default='linear', required=True)
    method_number = fields.Integer(string='Số kỳ khấu hao', default=60)
    method_period = fields.Integer(string='Số tháng mỗi kỳ', default=1)
    degressive_factor = fields.Float(string='Hệ số giảm dần', default=2.0)
    prorata = fields.Boolean(string='Khấu hao theo ngày')

    # --- LIÊN KẾT NHÂN SỰ ---
    employee_id = fields.Many2one('hr.employee', string='Người quản lý (custodian)', tracking=True)
    department_id = fields.Many2one('hr.department', string='Bộ phận sử dụng', tracking=True)

    # --- Tài khoản kế toán ---
    account_asset_id = fields.Many2one('account.account', string='TK tài sản (211)')
    account_depreciation_id = fields.Many2one('account.account', string='TK hao mòn (214)')
    account_expense_id = fields.Many2one('account.account', string='TK chi phí (627/641/642)')
    journal_id = fields.Many2one('account.journal', string='Sổ nhật ký')

    # --- Bảng khấu hao & bút toán ---
    depreciation_line_ids = fields.One2many(
        'asset.depreciation.line', 'asset_id', string='Dòng khấu hao')
    move_ids = fields.Many2many('account.move', string='Bút toán', compute='_compute_move_ids')
    move_line_ids = fields.Many2many('account.move.line', string='Dòng bút toán', compute='_compute_move_ids')
    entry_count = fields.Integer(string='Số bút toán', compute='_compute_move_ids')

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('open', 'Đang khấu hao'),
        ('paused', 'Tạm dừng'),
        ('close', 'Hết khấu hao'),
        ('disposed', 'Đã thanh lý'),
    ], string='Trạng thái', default='draft', tracking=True)

    # ------------------------------------------------------------------
    # COMPUTE
    # ------------------------------------------------------------------
    @api.depends('original_value', 'depreciation_line_ids.amount', 'depreciation_line_ids.move_id')
    def _compute_values(self):
        for asset in self:
            posted = asset.depreciation_line_ids.filtered(lambda l: l.move_id)
            depreciated = sum(posted.mapped('amount'))
            asset.depreciated_value = depreciated
            asset.value_residual = asset.original_value - depreciated

    @api.depends('depreciation_line_ids.move_id')
    def _compute_move_ids(self):
        for asset in self:
            moves = asset.depreciation_line_ids.mapped('move_id')
            asset.move_ids = moves
            asset.entry_count = len(moves)
            asset.move_line_ids = moves.mapped('line_ids')

    # ------------------------------------------------------------------
    # ONCHANGE
    # ------------------------------------------------------------------
    @api.onchange('category_id')
    def _onchange_category_id(self):
        cat = self.category_id
        if cat:
            self.method = cat.method
            self.method_number = cat.method_number
            self.method_period = cat.method_period
            self.degressive_factor = cat.degressive_factor
            self.prorata = cat.prorata
            self.account_asset_id = cat.account_asset_id
            self.account_depreciation_id = cat.account_depreciation_id
            self.account_expense_id = cat.account_expense_id
            self.journal_id = cat.journal_id

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.employee_id.department_id:
            self.department_id = self.employee_id.department_id

    # ------------------------------------------------------------------
    # CONSTRAINTS
    # ------------------------------------------------------------------
    @api.constrains('original_value', 'salvage_value', 'method_number')
    def _check_values(self):
        for asset in self:
            if asset.state != 'draft' and asset.original_value <= 0:
                raise ValidationError('Nguyên giá phải lớn hơn 0.')
            if asset.salvage_value < 0 or (asset.original_value and asset.salvage_value >= asset.original_value):
                raise ValidationError('Giá trị thanh lý phải nằm trong khoảng [0, nguyên giá).')
            if asset.method_number <= 0:
                raise ValidationError('Số kỳ khấu hao phải lớn hơn 0.')

    # ------------------------------------------------------------------
    # NGHIỆP VỤ KHẤU HAO
    # ------------------------------------------------------------------
    def compute_depreciation_board(self):
        """Sinh (lại) các dòng khấu hao dự kiến cho những kỳ CHƯA ghi sổ.
        Giữ nguyên các dòng đã có bút toán để không phá vỡ số liệu kế toán.
        """
        for asset in self:
            posted_lines = asset.depreciation_line_ids.filtered(lambda l: l.move_id)
            (asset.depreciation_line_ids - posted_lines).unlink()

            amount_to_depreciate = asset.original_value - asset.salvage_value
            already_depreciated = sum(posted_lines.mapped('amount'))
            residual_amount = amount_to_depreciate - already_depreciated

            posted_count = len(posted_lines)
            remaining_periods = asset.method_number - posted_count
            if remaining_periods <= 0 or residual_amount <= 0:
                continue

            # Ngày của dòng kế tiếp
            if posted_lines:
                last_date = max(posted_lines.mapped('depreciation_date'))
                next_date = last_date + relativedelta(months=asset.method_period)
            else:
                next_date = asset.date_start

            rounding = asset.currency_id.rounding or 0.01
            current_residual = residual_amount
            seq = posted_count
            new_lines = []

            for i in range(remaining_periods):
                seq += 1
                periods_left = remaining_periods - i
                if asset.method == 'linear':
                    amount = float_round(residual_amount / remaining_periods,
                                         precision_rounding=rounding)
                else:  # degressive (số dư giảm dần, tự chuyển sang đường thẳng khi có lợi hơn)
                    degressive_amount = current_residual * (asset.degressive_factor / asset.method_number)
                    linear_amount = current_residual / periods_left
                    amount = float_round(max(degressive_amount, linear_amount),
                                         precision_rounding=rounding)

                # Dòng cuối hoặc khi vượt số còn lại: gộp phần lẻ để khấu hao hết
                if i == remaining_periods - 1 or amount >= current_residual:
                    amount = current_residual
                current_residual = float_round(current_residual - amount, precision_rounding=rounding)

                new_lines.append((0, 0, {
                    'sequence': seq,
                    'name': '%s/%02d' % (next_date.year, next_date.month),
                    'amount': amount,
                    'depreciated_value': already_depreciated + (residual_amount - current_residual),
                    'remaining_value': current_residual,
                    'depreciation_date': next_date,
                }))
                next_date = next_date + relativedelta(months=asset.method_period)
                if current_residual <= 0:
                    break

            asset.write({'depreciation_line_ids': new_lines})
        return True

    @api.model
    def _cron_generate_depreciation_entries(self):
        """Tác vụ định kỳ (ir.cron): ghi sổ những dòng khấu hao đã tới hạn."""
        today = fields.Date.context_today(self)
        lines = self.env['asset.depreciation.line'].search([
            ('move_id', '=', False),
            ('depreciation_date', '<=', today),
            ('asset_id.state', '=', 'open'),
        ], order='depreciation_date, sequence, id')
        lines._create_moves()
        # Đóng các tài sản đã khấu hao hết
        for asset in lines.mapped('asset_id'):
            if asset.depreciation_line_ids and all(l.move_id for l in asset.depreciation_line_ids):
                asset.state = 'close'
        return True

    # ------------------------------------------------------------------
    # CHUYỂN TRẠNG THÁI
    # ------------------------------------------------------------------
    def action_confirm(self):
        for asset in self:
            if asset.original_value <= 0:
                raise UserError('Vui lòng nhập nguyên giá (> 0) trước khi đưa vào sử dụng.')
            if not asset.depreciation_line_ids:
                asset.compute_depreciation_board()
            asset.state = 'open'

    def action_pause(self):
        self.write({'state': 'paused'})

    def action_resume(self):
        self.write({'state': 'open'})

    def action_view_entries(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Bút toán khấu hao',
                'message': 'Xem chi tiết các dòng Nợ/Có ở tab "Bút toán đã ghi".',
                'type': 'info',
                'sticky': False,
            },
        }

    def action_ai_suggest(self):
        """Trợ lý AI: đoán nhóm tài sản từ tên và điền sẵn nhóm + tham số khấu hao."""
        self.ensure_one()
        from . import ai_suggester
        # Học thêm từ các tài sản đã có trong hệ thống (tên -> nhóm)
        extra = []
        for a in self.search([('category_id', '!=', False), ('id', '!=', self.id)], limit=500):
            if a.name and a.category_id:
                extra.append((a.name, a.category_id.name))
        result = ai_suggester.suggest(self.name or '', extra_samples=extra)
        label = result.get('label')
        conf = result.get('confidence') or 0.0
        months = result.get('months')
        backend = result.get('backend')

        body = []
        if label:
            category = self.env['asset.category'].search([('name', 'ilike', label)], limit=1)
            if category:
                self.write({
                    'category_id': category.id,
                    'method': category.method,
                    'method_number': category.method_number,
                    'method_period': category.method_period,
                    'degressive_factor': category.degressive_factor,
                    'prorata': category.prorata,
                    'account_asset_id': category.account_asset_id.id,
                    'account_depreciation_id': category.account_depreciation_id.id,
                    'account_expense_id': category.account_expense_id.id,
                    'journal_id': category.journal_id.id,
                })
                body.append('Đã tự chọn nhóm: <b>%s</b>' % category.name)
            else:
                body.append('Gợi ý loại: <b>%s</b> (chưa có nhóm tương ứng, bạn có thể tạo nhóm này)' % label)
                if months and not self.method_number:
                    self.write({'method_number': months})
                    body.append('Gợi ý số kỳ khấu hao: %s tháng' % months)
            body.insert(0, '🤖 AI dự đoán: <b>%s</b> — độ tin cậy %.1f%%' % (label, conf))
            ranking = result.get('ranking') or []
            if len(ranking) > 1:
                body.append('Xếp hạng: ' + ', '.join('%s (%.0f%%)' % (l, p) for l, p in ranking))
        else:
            body.append('🤖 Chưa đủ dữ liệu để AI gợi ý.')
        body.append('<i>Mô hình: %s</i>' % backend)
        self.message_post(body='<br/>'.join(body))
        # Mở lại form để thấy nhóm vừa được điền
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'asset.asset',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_dispose(self):
        """Thanh lý: ghi giảm tài sản khỏi sổ.
        Định khoản: Nợ 214 (hao mòn lũy kế) + Nợ 811/642 (giá trị còn lại) / Có 211 (nguyên giá).
        """
        for asset in self:
            journal = asset.journal_id or asset.category_id.journal_id
            if not (asset.account_asset_id and asset.account_depreciation_id and journal):
                raise UserError('Tài sản %s thiếu cấu hình tài khoản/sổ nhật ký để thanh lý.' % asset.name)
            depreciated = asset.depreciated_value
            residual = asset.value_residual
            line_ids = [
                (0, 0, {  # giảm hao mòn lũy kế
                    'name': 'Thanh lý: %s' % asset.name,
                    'account_id': asset.account_depreciation_id.id,
                    'debit': depreciated, 'credit': 0.0,
                }),
                (0, 0, {  # giảm nguyên giá
                    'name': 'Thanh lý: %s' % asset.name,
                    'account_id': asset.account_asset_id.id,
                    'debit': 0.0, 'credit': asset.original_value,
                }),
            ]
            if residual > 0:
                # Giá trị còn lại đưa vào chi phí (thực tế nên cấu hình TK 811 riêng)
                line_ids.append((0, 0, {
                    'name': 'Giá trị còn lại: %s' % asset.name,
                    'account_id': asset.account_expense_id.id,
                    'debit': residual, 'credit': 0.0,
                }))
            move = self.env['account.move'].create({
                'journal_id': journal.id,
                'date': fields.Date.context_today(self),
                'ref': 'Thanh lý %s' % asset.name,
                'move_type': 'entry',
                'line_ids': line_ids,
            })
            move.action_post()
            asset.state = 'disposed'
        return True
