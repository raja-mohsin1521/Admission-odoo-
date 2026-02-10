from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MeritSelectionRegister(models.Model):
    _name = 'merit.selection.register'
    _description = 'Master Merit Selection'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Merit List Title", required=True)
    academic_session_id = fields.Many2one('academy.academic.session', string="Session", required=True)
    academic_term_id = fields.Many2one('academy.term.scheme', string="Term", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Merit Calculated'),
        ('allotted', '1st List Published'),
        ('second_list', '2nd List Published'),
        ('finalized', 'Finalized')
    ], default='draft', tracking=True)

    line_ids = fields.One2many('merit.selection.line', 'register_id', string="Merit Rankings")

    _unique_merit_list = models.Constraint(
        'UNIQUE(academic_session_id, academic_term_id)',
        'A merit list already exists for this Session and Term!'
    )

    def action_generate_merit_list(self):
        self.line_ids.unlink()
        applications = self.env['student.application'].search([
            ('academic_session_id', '=', self.academic_session_id.id),
            ('academic_term_id', '=', self.academic_term_id.id),
            ('register_id.state', '=', 'merit'),
            ('state', '=', 'approve')
        ])

        if not applications:
            raise UserError(_("No approved applications found in 'Merit' stage."))

        student_best_apps = {}
        for app in applications:
            sid = app.applicant_id.id
            if sid not in student_best_apps or app.aggregate_score > student_best_apps[sid].aggregate_score:
                student_best_apps[sid] = app

        sorted_apps = sorted(student_best_apps.values(), key=lambda x: x.aggregate_score, reverse=True)
        lines = []
        for index, app in enumerate(sorted_apps, start=1):
            lines.append((0, 0, {
                'rank': index,
                'applicant_id': app.applicant_id.id,
                'application_id': app.id,
                'aggregate_score': app.aggregate_score,
                'is_allocated': False
            }))
        self.line_ids = lines
        self.state = 'calculated'

    def action_allot_seats(self):
        self._process_allocation()
        self.state = 'allotted'

    def action_generate_second_list(self):
        self._process_allocation()
        self.state = 'second_list'

    def _process_allocation(self):
        allocation_master = self.env['academy.seat.allocation'].search([
            ('academic_session_id', '=', self.academic_session_id.id),
            ('academic_term_id', '=', self.academic_term_id.id),
            ('state', '=', 'confirmed')
        ], limit=1)

        if not allocation_master:
            raise UserError(_("No confirmed Seat Allocation found."))

        capacities = {}
        for l in allocation_master.line_ids:
            currently_occupied = len(self.line_ids.filtered(
                lambda x: x.is_allocated and x.allotted_program_id.id == l.program_id.id
            ))
            capacities[l.program_id.id] = {
                'total': l.total_seats,
                'occupied': currently_occupied,
                'line': l
            }

        for line in self.line_ids.filtered(lambda x: not x.is_allocated).sorted('rank'):
            preferences = line.application_id.preference_line_ids.sorted('preference_no')
            
            allotted_program = False
            for pref in preferences:
                p_id = pref.program_id.id
                if p_id in capacities and capacities[p_id]['occupied'] < capacities[p_id]['total']:
                    allotted_program = pref.program_id
                    capacities[p_id]['occupied'] += 1
                    
                    alloc_line = capacities[p_id]['line']
                    alloc_line.occupied_seats = capacities[p_id]['occupied']
                    alloc_line.closing_merit = line.aggregate_score
                    if alloc_line.occupied_seats == 1:
                         alloc_line.opening_merit = line.aggregate_score
                    
                    break
            
            if allotted_program:
                line.write({
                    'allotted_program_id': allotted_program.id,
                    'is_allocated': True
                })

class MeritSelectionLine(models.Model):
    _name = 'merit.selection.line'
    _description = 'Merit Ranking Line'
    _order = 'rank asc'

    register_id = fields.Many2one('merit.selection.register', ondelete='cascade')
    rank = fields.Integer(string="Rank", readonly=True)
    applicant_id = fields.Many2one('student.applicant', string="Student", readonly=True)
    application_id = fields.Many2one('student.application', string="Source App", readonly=True)
    aggregate_score = fields.Float(string="Aggregate", digits=(16, 2), readonly=True)
    allotted_program_id = fields.Many2one('academy.program', string="Allotted Program", readonly=True)
    is_allocated = fields.Boolean(string="Confirmed", default=False)