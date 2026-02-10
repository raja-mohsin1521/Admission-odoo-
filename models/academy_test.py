from odoo import models, fields, api


class AcademyTestType(models.Model):
    _name = 'academy.test.type'
    _description = 'Test Type'
    
    name = fields.Char(string="Test Type", required=True)
    code = fields.Char(string="Code", required=True)
    active = fields.Boolean(default=True)

    _unique_code = models.Constraint(
    'UNIQUE(code)',
    'The Test Type Code must be unique!')


class AcademyTestCenter(models.Model):
    _name = 'academy.test.center'
    _description = 'Test Center'
    
    name = fields.Char(string="City/Center Name", required=True)
    code = fields.Char(string="City Code", required=True)
    address = fields.Text(string="Full Address")
    
    register_id = fields.Many2one('admission.register', string="Admission Register")
    test_type_id = fields.Many2one('academy.test.type', string="Test Type")
    session_id = fields.Many2one('academy.academic.session', string="Session")
    
    timing_ids = fields.One2many('academy.test.timing', 'center_id', string="Test Timings")
    count = fields.Integer(string="Total Registered", compute="_compute_total_count")
    
    _unique_code = models.Constraint(
    'UNIQUE(code)',
    'The Test Center Code must be unique!'
)


  

    @api.depends('timing_ids.count')
    def _compute_total_count(self):
        for rec in self:
            rec.count = sum(rec.timing_ids.mapped('count'))

class AcademyTestTiming(models.Model):
    _name = 'academy.test.timing'
    _description = 'Test Timing Slots'
    _rec_name = 'display_name'

    center_id = fields.Many2one('academy.test.center', string="Test Center", ondelete='cascade')
    test_date = fields.Date(string="Test Date", required=True)
    test_time = fields.Float(string="Test Time", required=True)
    
    capacity = fields.Integer(string="Capacity", default=500)
    count = fields.Integer(string="Registered Count", compute="_compute_registration_count")
    active = fields.Boolean(string="Active", default=True)
    
    career_id = fields.Many2one('academy.career', string="Career", required=True)
    degree_ids = fields.Many2many('academy.degree', string="Eligible Degrees")
    
    display_name = fields.Char(compute="_compute_display_name")

    @api.depends('test_date', 'test_time')
    def _compute_display_name(self):
        for rec in self:
            hour = int(rec.test_time)
            minute = int(round((rec.test_time % 1) * 60))
            rec.display_name = f"{rec.test_date} at {hour:02d}:{minute:02d}"

    def _compute_registration_count(self):
        for rec in self:
            rec.count = self.env['student.application'].search_count([
                ('test_slot_id', '=', rec.id)
            ])