from odoo import models, fields


class AcademicSession(models.Model):
    _name = 'academy.academic.session'
    _description = 'Academic Session'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    description = fields.Text()
    active = fields.Boolean(default=True)

    term_scheme_ids = fields.One2many(
        'academy.term.scheme',
        'session_id',
        string='Term Scheme'
    )

    _unique_code = models.Constraint(
    'UNIQUE(code)',
    'The Academic Session Code must be unique!'
    )
