{
    "name": "Odoo 19 Academy",
    "summary": "Starter custom module for Odoo 19 — simple Academy app",
    "version": "19.0.1.0.0",
    "category": "Education",
    "author": "Raja Mohsin",
    "website": "https://sqride.com/",
    "license": "LGPL-3",
    "depends": [
        "base", 
        "web", 
        "mail",          # REQUIRED: For mail.thread and mail.activity.mixin
        "portal", 
        "auth_signup",
        "website"
    ],
    "data": [
        # 1. Security First
        "security/security.xml",
        "security/ir.model.access.csv",
        'data/ir_sequence_data.xml',

        # 2. Base Configuration Views (Actions must be defined here first)
        "views/campus_views.xml",
        "views/career_views.xml",
        "views/degree_views.xml",
        "views/academic_session_views.xml",
        "views/term_scheme_views.xml",
        "views/academy_program_views.xml",
        "views/course_views.xml",
        "views/admission_register_views.xml",
        "views/academy_test_views.xml",
        "views/test_score_views.xml",
        
        "views/res_config_settings_views.xml",
        # 3. Application & Student Views
        "views/aggregate_calculation_views.xml",
        "views/student_views.xml",
        "views/student_application_views.xml",
'views/fee_voucher_upload.xml',
'views/select_testcenter_portal.xml',
'views/academy_seat_allocation_views.xml',
'views/merit_selection_views.xml',
        # 4. MENUS (Must be loaded AFTER the actions/views they reference)
        "views/academy_menu.xml", 

        # 5. Templates & Portals
        "views/portal_templates.xml",
        "views/signup_templates.xml",
        "report/admission_challan_report.xml",
        "report/admit_card_report.xml",
    ],
    "installable": True,
    "application": True,
}