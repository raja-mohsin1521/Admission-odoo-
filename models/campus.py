from odoo import models, fields, api


class AcademyCampus(models.Model):
    _name = 'academy.campus'
    _description = 'Campus'

    name = fields.Char(string="Campus Name", required=True)
    code = fields.Char(string="Campus Code", required=True, index=True)
    institute_ids = fields.One2many('academy.institute', 'campus_id', string="Institutes")
    
    _unique_code = models.Constraint(
    'UNIQUE(code)',
    'The Campus Code must be unique!'
)


    

class AcademyInstitute(models.Model):
    _name = 'academy.institute'
    _description = 'Institute'

    name = fields.Char(string="Institute Name", required=True)
    code = fields.Char(string="Institute Code", required=True, index=True)
    phone = fields.Char(string="Phone")
    website = fields.Char(string="Website")
    campus_id = fields.Many2one('academy.campus', string="Campus", required=True)
    department_ids = fields.One2many('academy.department', 'institute_id', string="Departments")
    
    
    _unique_code = models.Constraint(
    'UNIQUE(code)',
    'The Institute Code must be unique!'
)


 

class AcademyDepartment(models.Model):
    _name = 'academy.department'
    _description = 'Department'

    name = fields.Char(string="Department Name", required=True)
    code = fields.Char(string="Department Code", required=True, index=True)
    institute_id = fields.Many2one('academy.institute', string="Institute", required=True)
    campus_id = fields.Many2one(
        'academy.campus', 
        related='institute_id.campus_id', 
        string="Campus", 
        readonly=True, 
        store=True
    )
    _unique_code = models.Constraint(
    'UNIQUE(code)',
    'The Department Code must be unique!'
)


  