from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    cnic = fields.Char(string="CNIC")