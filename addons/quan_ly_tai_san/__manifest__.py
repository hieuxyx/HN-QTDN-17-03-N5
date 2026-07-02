# -*- coding: utf-8 -*-
{
    'name': "Quản lý tài sản",
    'summary': "Quản lý tài sản, khấu hao và tự động ghi sổ kế toán",
    'description': "Quản lý loại tài sản, tài sản, sinh bảng khấu hao đường thẳng; tự động tạo bút toán Nợ 642/Có 214 sang module Kế toán khi ghi sổ khấu hao (Mức 2).",
    'author': "Nhom XX - FIT DNU",
    'category': 'Accounting',
    'version': '15.0.2.0.0',
    'depends': ['base', 'nhan_su', 'ke_toan'],
    'data': [
        'security/ir.model.access.csv',
        'views/loai_tai_san.xml',
        'views/tai_san.xml',
        'views/menu.xml',
        'data/cron.xml',
    ],
    'application': True,
    'installable': True,
}
