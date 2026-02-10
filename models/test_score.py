from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AdmissionTestScore(models.Model):
    _name = 'admission.test.score'
    _description = 'Student Test Scores'
    _rec_name = 'application_id'

    application_id = fields.Many2one(
        'student.application',
        string="Application",
        required=True,
        ondelete='cascade'
    )

    applicant_id = fields.Many2one(
        'student.applicant',
        related='application_id.applicant_id',
        store=True,
        readonly=True
    )

    register_id = fields.Many2one(
        'admission.register',
        related='application_id.register_id',
        store=True,
        readonly=True
    )

    test_slot_id = fields.Many2one(
        'academy.test.timing',
        related='application_id.test_slot_id',
        store=True,
        readonly=True
    )

    test_date = fields.Date(
        related='test_slot_id.test_date',
        store=True,
        readonly=True
    )

    register_state = fields.Selection(
        related='register_id.state',
        readonly=True
    )

    max_marks = fields.Float(default=100.0)
    obtained_marks = fields.Float(default=0.0)

    percentage = fields.Float(
        compute='_compute_percentage',
        store=True
    )

    aggrigate_score = fields.Float(
        related='application_id.aggregate_score',
        store=True,
        readonly=True
    )

    attendance_status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent')
    ], compute='_compute_attendance', store=True)

    
    _sql_constraints = [
        (
            'unique_application',
            'unique(application_id)',
            'Test score already exists for this application!'
        )
    ]


    @api.depends('obtained_marks')
    def _compute_attendance(self):
        for rec in self:
            rec.attendance_status = 'present' if rec.obtained_marks > 0 else 'absent'


    @api.depends('obtained_marks', 'max_marks')
    def _compute_percentage(self):
        for rec in self:
            rec.percentage = (rec.obtained_marks / rec.max_marks * 100) if rec.max_marks else 0.0


    @api.constrains('obtained_marks', 'max_marks')
    def _check_marks(self):
        for rec in self:
            if rec.obtained_marks > rec.max_marks:
                raise ValidationError(_("Obtained marks cannot be greater than maximum marks."))


    @api.constrains('register_id')
    def _check_register_lock(self):
        for rec in self:
            if rec.register_id.state == 'merit':
                raise ValidationError(_("You cannot modify test scores because the register is in Merit stage."))



class StudentApplication(models.Model):
    _inherit = 'student.application'

    test_score_ids = fields.One2many('admission.test.score', 'application_id', string="Test Scores")

    def action_approve(self):
        res = super(StudentApplication, self).action_approve()
        for rec in self:
            # Create a blank score record when application is approved
            existing_score = self.env['admission.test.score'].search([
                ('applicant_id', '=', rec.applicant_id.id),
                ('register_id', '=', rec.register_id.id)
            ], limit=1)
            
            if not existing_score:
                self.env['admission.test.score'].create({
                    'application_id': rec.id,
                    'obtained_marks': 0.0,
                    'max_marks': 100.0,
                    'attendance_status': 'absent'
                })
        return res