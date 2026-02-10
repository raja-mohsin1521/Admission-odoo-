from odoo import models, fields, api, _

class AcademySeatAllocation(models.Model):
    _name = 'academy.seat.allocation'
    _description = 'Seat Allocation Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Allocation Title", required=True, tracking=True)
    academic_session_id = fields.Many2one('academy.academic.session', string="Session", required=True)
    academic_term_id = fields.Many2one('academy.term.scheme', string="Term", required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], default='draft', tracking=True)
    line_ids = fields.One2many('academy.seat.allocation.line', 'allocation_id', string="Program Capacities")
    _unique_allocation = models.Constraint(
        'UNIQUE(academic_session_id, academic_term_id)',
        'A seat allocation record already exists for this Session and Term!'
    )

    
    @api.onchange('academic_session_id', 'academic_term_id')
    def _onchange_session_term(self):
        if self.academic_session_id and self.academic_term_id:
            registers = self.env['admission.register'].search([
                ('academic_session_id', '=', self.academic_session_id.id),
                ('academic_term_id', '=', self.academic_term_id.id)
            ])
            programs = registers.mapped('program_ids')
            lines = []
            for program in programs:
                lines.append((0, 0, {
                    'program_id': program.id,
                    'total_seats': 0
                }))
            self.line_ids = [(5, 0, 0)] + lines

    def action_confirm(self):
        self.write({'state': 'confirmed'})

class AcademySeatAllocationLine(models.Model):
    _name = 'academy.seat.allocation.line'
    _description = 'Program Seat Capacity'

    allocation_id = fields.Many2one('academy.seat.allocation', ondelete='cascade')
    program_id = fields.Many2one('academy.program', string="Program", required=True)
    total_seats = fields.Integer(string="No. of Seats", default=0)
    opening_merit = fields.Float(string="Opening Merit", digits=(16, 2), readonly=True)
    closing_merit = fields.Float(string="Closing Merit", digits=(16, 2), readonly=True)
    occupied_seats = fields.Integer(string="Occupied", readonly=True)