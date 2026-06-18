# -*- coding: utf-8 -*-
{
    'name': 'Quản lý tài sản & Khấu hao',
    'version': '15.0.3.2.0',
    'category': 'Accounting/Accounting',
    'summary': 'Quản lý TSCĐ, tự động khấu hao, ghi sổ cái, ngân sách mua sắm, tích hợp Nhân sự',
    'description': """
Module quản lý tài sản cố định tích hợp Kế toán và Nhân sự (Odoo 15).
- Quản lý hồ sơ tài sản, nhóm tài sản
- Tự động tính & ghi sổ khấu hao định kỳ (ir.cron)
- Cấp phát/bàn giao tài sản cho nhân viên, ràng buộc khi nghỉ việc
- Đề xuất mua sắm + ngân sách theo phòng ban + báo cáo dòng tiền
- Thanh lý tài sản và hạch toán giảm
    """,
    'author': 'Nhóm sinh viên',
    'website': 'https://github.com/<your-account>/<repo>',
    'depends': ['base', 'mail', 'hr', 'account'],
    'data': [
        'security/asset_security.xml',
        'security/ir.model.access.csv',
        'data/asset_sequence.xml',
        'data/asset_cron.xml',
        'views/asset_category_views.xml',
        'views/asset_asset_views.xml',
        'views/asset_allocation_views.xml',
        'views/asset_budget_views.xml',
        'views/asset_purchase_request_views.xml',
        'views/asset_report_views.xml',
        'views/hr_employee_views.xml',
        'views/asset_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
