from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    admission_fee = fields.Float(
        string="Registration Fee",
        config_parameter='odoo19_academy.admission_fee',
        
    )
    international_admission_fee = fields.Float(
        string="International Fee",
        config_parameter='odoo19_academy.international_fee',
   
    )
    
    # Three separate bank account fields
    bank_account_title_1 = fields.Char(
        string="Bank Account Title 1",
        config_parameter='odoo19_academy.bank_account_title_1',
        default="NUTECH Academy - HBL"
    )
    bank_account_title_2 = fields.Char(
        string="Bank Account Title 2",
        config_parameter='odoo19_academy.bank_account_title_2'
    )
    bank_account_title_3 = fields.Char(
        string="Bank Account Title 3",
        config_parameter='odoo19_academy.bank_account_title_3'
    )