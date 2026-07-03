# -*- coding: utf-8 -*-
{
    'name': "Quản lý tài sản",
    'summary': "Quản lý tài sản, khấu hao, tự động ghi sổ kế toán, AI phân loại + OCR hóa đơn + Chatbot + Telegram",
    'description': "Mức 1: 3 module tích hợp. Mức 2: tự động ghi sổ khấu hao (Nợ 642/Có 214). "
                   "Mức 3: AI Naive Bayes phân loại; OCR hóa đơn (Gemini) tạo tài sản; Chatbot hỏi-đáp (Gemini); "
                   "Telegram thông báo khấu hao. API key/token đọc từ Tham số hệ thống.",
    'author': "Nhom XX - FIT DNU",
    'category': 'Accounting',
    'version': '15.0.4.0.0',
    'depends': ['base', 'nhan_su', 'ke_toan'],
    'data': [
        'security/ir.model.access.csv',
        'data/config_params.xml',
        'views/loai_tai_san.xml',
        'views/tai_san.xml',
        'views/nhap_hoa_don.xml',
        'views/tro_ly_ai.xml',
        'views/menu.xml',
        'data/cron.xml',
    ],
    'application': True,
    'installable': True,
}
