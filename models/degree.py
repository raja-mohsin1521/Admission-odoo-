from odoo import models, fields
from odoo.models import Constraint

class AcademicLevel(models.Model):
    _name = 'academy.level'
    _description = 'Academic Level'
    
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    degree_ids = fields.One2many('academy.degree', 'level_id', string='Degrees')

    _sql_constraints = [
        Constraint('unique(code)', 'The Academic Level Code must be unique!')
    ]

class AcademicDegree(models.Model):
    _name = 'academy.degree'
    _description = 'Academic Degree'
    
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    color = fields.Integer(string="Color Index")
    year_of_education = fields.Integer(string="Year of Education")
    level_id = fields.Many2one('academy.level', string="Degree Level", required=True)
    specialization_ids = fields.One2many('academy.specialization', 'degree_id', string='Specializations')
    offering_ids = fields.One2many('academy.program.eligibility', 'degree_id', string='Programs Offering This Degree')

    _sql_constraints = [
        Constraint('unique(code)', 'The Academic Degree Code must be unique!')
    ]

class AcademicSpecialization(models.Model):
    _name = 'academy.specialization'
    _description = 'Academic Specialization'
    
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    degree_id = fields.Many2one('academy.degree', string="Degree", required=True, ondelete='cascade')

    _sql_constraints = [
        Constraint('unique(code)', 'The Academic Specialization Code must be unique!')
    ]