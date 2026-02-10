from odoo import models, fields, api, _, Command

from odoo.exceptions import ValidationError

class AcademyProgram(models.Model):
    _name = 'academy.program'
    _description = 'Academic Program'

    name = fields.Char(string="Name", required=True, index=True)
    code = fields.Char(string="Code", index=True)
    duration = fields.Char(string="Duration", default="4 Years")
    effective_date = fields.Date(string="Effective Date")
    
    dept_id = fields.Many2one('academy.department', string="Department")
    career_id = fields.Many2one('academy.career', string="Career")
    campus_id = fields.Many2one('academy.campus', string="Campus")
    
    eligibility_ids = fields.Many2many(
        'academy.program.eligibility',
        'program_eligibility_rel',
        'program_id',
        'eligibility_id',
        string="Eligibility Criteria"
    )

    _unique_code = models.Constraint(
        'UNIQUE(code)',
        'The Academic Program Code must be unique!'
    )

class AcademyProgramEligibility(models.Model):
    _name = 'academy.program.eligibility'
    _description = 'Program Eligibility'

    name = fields.Char(string="Criteria Name", required=True)
    code = fields.Char(string="Criteria Code", required=True, index=True)
    
    career_id = fields.Many2one('academy.career', string="Career")
    degree_id = fields.Many2one('academy.degree', string="Eligible Degree", required=True)
    specialization_ids = fields.Many2many('academy.specialization', string="Specializations")
    
    evaluation_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('cgpa', 'CGPA')
    ], string="Evaluation Type", default='percentage', required=True)

    eligibility_percentage_min = fields.Float(string="Min Percentage")
    eligibility_percentage_max = fields.Float(string="Max Percentage", default=100.0)
    eligibility_cgpa_min = fields.Float(string="Min CGPA")
    eligibility_cgpa_max = fields.Float(string="Max CGPA", default=4.0)
    
    program_ids = fields.Many2many(
        'academy.program',
        'program_eligibility_rel',
        'eligibility_id',
        'program_id',
        string="Programs",
        readonly=True
    )

    _unique_code = models.Constraint(
    'UNIQUE(code)',
    'The Eligibility Criteria Code must be unique!')

    @api.constrains('eligibility_percentage_min', 'eligibility_percentage_max', 
                    'eligibility_cgpa_min', 'eligibility_cgpa_max', 'evaluation_type')
    def _check_eligibility_ranges(self):
        for record in self:
            if record.evaluation_type == 'percentage':
                if record.eligibility_percentage_min > record.eligibility_percentage_max:
                    raise ValidationError(_("Minimum percentage cannot be greater than maximum percentage."))
            elif record.evaluation_type == 'cgpa':
                if record.eligibility_cgpa_min > record.eligibility_cgpa_max:
                    raise ValidationError(_("Minimum CGPA cannot be greater than maximum CGPA."))

    @api.onchange('degree_id')
    def _onchange_degree_id(self):
        if self.degree_id:
            self.specialization_ids = [Command.clear()]
            return {'domain': {'specialization_ids': [('degree_id', '=', self.degree_id.id)]}}
        return {'domain': {'specialization_ids': []}}