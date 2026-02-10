from odoo import models, fields
from odoo.models import Constraint

class Career(models.Model):
    _name = 'academy.career'
    _description = 'Career'
    _rec_name = 'name'

    name = fields.Char(string='Career Name', required=True)
    short_code = fields.Char(string='Short Code', required=True, index=True)
    description = fields.Text(string='Description')

    _sql_constraints = [
        Constraint('unique(short_code)', 'The Career Code must be unique!')
    ]