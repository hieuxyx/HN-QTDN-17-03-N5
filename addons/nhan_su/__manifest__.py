# -*- coding: utf-8 -*-
{
    'name': "nhan_su",
    'summary': "Quản lý nhân sự (đã sửa lỗi và bổ sung phòng ban/chức vụ/trạng thái)",
    'description': "Module HRM nền tảng, đóng vai trò dữ liệu gốc về nhân viên cho các module khác.",
    'author': "Nhom XX - FIT DNU",
    'website': "https://github.com/FIT-DNU/Business-Internship",
    'category': 'Human Resources',
    'version': '15.0.1.0.0',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/chuc_vu.xml',
        'views/don_vi.xml',
        'views/nhan_vien.xml',
        'views/lich_su_cong_tac.xml',
        'views/chung_chi_bang_cap.xml',
        'views/danh_sach_chung_chi_bang_cap.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'application': True,
    'installable': True,
}
