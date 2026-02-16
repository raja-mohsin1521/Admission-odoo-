from odoo import models, fields, api, _

class AdmissionRegister(models.Model):
    _name = 'admission.register'
  
    _description = 'Admission Register'
    _order = 'start_date desc'

    name = fields.Char(string="Register Name", required=True)
    start_date = fields.Date(string="Start Date", default=fields.Date.context_today, required=True)
    end_date = fields.Date(string="End Date", required=True)
    line_ids = fields.One2many('merit.selection.line', 'register_id', string='Lines')
    dob_min = fields.Date(string="DOB Minimum")
    dob_max = fields.Date(string="DOB Maximum")
    min_education_year = fields.Integer(string="Minimum Education Year", default=12)
    preferences_allowed = fields.Integer(string="Preferences Allowed", default=0)
    
    career_id = fields.Many2one('academy.career', string="Career")
    academic_session_id = fields.Many2one('academy.academic.session', string="Academic Session", required=True)
    academic_term_id = fields.Many2one('academy.term.scheme', string="Academic Term", required=True)
    
    eligibility_file = fields.Binary(string="Eligibility criteria Image")
    test_name = fields.Char(string="Test Name")
    calculation_method = fields.Many2one('academy.aggregate', string="Merit Calculation Method", required=True)
    
    
    

    program_ids = fields.Many2many(
        'academy.program', 
        'admission_register_program_rel', 
        'register_id', 
        'program_id', 
        string="Programs"
    )

    undertaking = fields.Html(string="Undertaking")
    active = fields.Boolean(default=True)
    _unique_code = models.Constraint(
    'UNIQUE(code)',
    'The Admission Register Name must be unique!'
)

    
   

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('gathering', 'Application Gathering'),
        ('stopped', 'Stop Gathering'),
        ('merit', 'Merit Process'),
        ('done', 'Done')
    ], string='Status', default='draft', required=True)

    def action_confirm(self):
        self.state = 'confirmed'

    def action_gathering(self):
        self.state = 'gathering'
        
    def action_stop_gathering(self):
        self.state = 'stopped'

    def action_merit(self):
        self.state = 'merit'

    def action_done(self):
        self.state = 'done'

    def action_reset(self):
        self.state = 'draft'