# -*- coding: utf-8 -*-
{
    'name': "Kế toán - Tài chính",
    'summary': "Hệ thống tài khoản, bút toán và sổ cái",
    'description': "Module kế toán đơn giản: tài khoản, bút toán, sổ cái; nhận bút toán khấu hao từ module Quản lý tài sản.",
    'author': "Nhom XX - FIT DNU",
    'category': 'Accounting',
    'version': '15.0.1.0.0',
    'depends': ['base', 'nhan_su'],
    'data': [
        'security/ir.model.access.csv',
        'data/ke_toan_data.xml',
        'views/tai_khoan_ke_toan.xml',
        'views/but_toan.xml',
        'views/menu.xml',
    ],
    'application': True,
    'installable': True,
}
