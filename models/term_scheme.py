from odoo import models, fields
from odoo.models import Constraint

class TermScheme(models.Model):
    _name = 'academy.term.scheme'
    _description = 'Term Scheme'

    session_id = fields.Many2one(
        'academy.academic.session',
        'Academic Session',
        ondelete='cascade',
        required=True
    )

    name = fields.Char(string='Name', required=True)
    short_code = fields.Char(string='Short Code', required=True)

    current_term = fields.Boolean(string='Current Term', required=True)

    description = fields.Text(string='Description')

    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)

    _sql_constraints = [
        Constraint('unique(short_code)', 'The Academic Term Code must be unique!')
    ]