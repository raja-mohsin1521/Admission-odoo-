from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MeritSelectionRegister(models.Model):
    _name = 'merit.selection.register'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    academic_session_id = fields.Many2one('academy.academic.session', required=True)
    academic_term_id = fields.Many2one('academy.term.scheme', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('done', 'Closed')
    ], default='draft')

    merit_round = fields.Integer(default=0)

    line_ids = fields.One2many(
        'merit.selection.line',
        'register_id'
    )

    excluded_applicant_ids = fields.Many2many(
        'student.applicant'
    )

    _sql_constraints = [
        ('unique_merit',
         'UNIQUE(academic_session_id, academic_term_id)',
         'Merit already exists for this Session and Term!')
    ]

    def action_generate_merit(self):
        self.ensure_one()

        if self.state != 'draft':
            raise UserError(_("Already started."))

        self.line_ids.unlink()
        self.excluded_applicant_ids = [(5, 0, 0)]
        self.merit_round = 0

        applications = self.env['student.application'].search([
            ('academic_session_id', '=', self.academic_session_id.id),
            ('academic_term_id', '=', self.academic_term_id.id),
            ('state', '=', 'approve')
        ])

        if not applications:
            raise UserError(_("No approved applications found."))

        best = {}
        for app in applications:
            sid = app.applicant_id.id
            if sid not in best or app.aggregate_score > best[sid].aggregate_score:
                best[sid] = app

        sorted_apps = sorted(best.values(), key=lambda x: x.aggregate_score, reverse=True)

        lines = []
        for rank, app in enumerate(sorted_apps, start=1):
            lines.append((0, 0, {
                'rank': rank,
                'applicant_id': app.applicant_id.id,
                'application_id': app.id,
                'aggregate_score': app.aggregate_score,
                'merit_round': 0,
                'is_allocated': False
            }))

        self.line_ids = lines
        self.state = 'running'

        self.action_next_merit()

    def action_next_merit(self):
        self.ensure_one()

        if self.state != 'running':
            raise UserError(_("Not running."))

        if self._all_seats_filled():
            raise UserError(_("All seats filled. Close admission."))

        self.merit_round += 1
        self._allocate_round()

    def action_close_admission(self):
        if not self._all_seats_filled():
            raise UserError(_("Seats still available."))
        self.state = 'done'

    def _get_allocation(self):
        alloc = self.env['academy.seat.allocation'].search([
            ('academic_session_id', '=', self.academic_session_id.id),
            ('academic_term_id', '=', self.academic_term_id.id),
            ('state', '=', 'confirmed')
        ], limit=1)

        if not alloc:
            raise UserError(_("No confirmed seat allocation."))

        return alloc

    def _all_seats_filled(self):
        alloc = self._get_allocation()
        for l in alloc.line_ids:
            if l.occupied_seats < l.total_seats:
                return False
        return True

    def _allocate_round(self):
        alloc = self._get_allocation()

        for l in alloc.line_ids:
            l.occupied_seats = 0

        capacities = {}
        for l in alloc.line_ids:
            capacities[l.program_id.id] = {
                'total': l.total_seats,
                'occupied': 0,
                'line': l
            }

        for line in self.line_ids.sorted('rank'):

            if line.merit_round:
                pid = line.allotted_program_id.id
                if pid in capacities:
                    capacities[pid]['occupied'] += 1
                    capacities[pid]['line'].occupied_seats = capacities[pid]['occupied']
                continue

            if line.applicant_id.id in self.excluded_applicant_ids.ids:
                continue

            preferences = line.application_id.preference_line_ids.sorted('preference_no')

            for pref in preferences:
                pid = pref.program_id.id

                if pid in capacities and capacities[pid]['occupied'] < capacities[pid]['total']:

                    capacities[pid]['occupied'] += 1
                    cap_line = capacities[pid]['line']
                    cap_line.occupied_seats = capacities[pid]['occupied']

                    line.write({
                        'allotted_program_id': pid,
                        'is_allocated': True,
                        'merit_round': self.merit_round
                    })
                    break


class MeritSelectionLine(models.Model):
    _name = 'merit.selection.line'
    _order = 'rank asc'

    register_id = fields.Many2one('merit.selection.register', ondelete='cascade')
    rank = fields.Integer(readonly=True)
    applicant_id = fields.Many2one('student.applicant', readonly=True)
    application_id = fields.Many2one('student.application', readonly=True)
    aggregate_score = fields.Float(readonly=True)

    allotted_program_id = fields.Many2one('academy.program', readonly=True)
    is_allocated = fields.Boolean()
    merit_round = fields.Integer(readonly=True)

    def action_withdraw(self):
        for rec in self:
            register = rec.register_id
            register.excluded_applicant_ids = [(4, rec.applicant_id.id)]
            rec.unlink()
