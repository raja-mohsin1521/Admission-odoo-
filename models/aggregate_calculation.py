from odoo import models, fields, api, _

from odoo.exceptions import ValidationError

class AcademyAggregate(models.Model):
    _name = 'academy.aggregate'
    _description = 'Aggregate Calculation'

    name = fields.Char(string="Calculation Name", required=True)
    code = fields.Char(string="Code", required=True, index=True)
    line_ids = fields.One2many('academy.aggregate.line', 'aggregate_id', string="Criteria Lines")
    
    total_weight = fields.Float(
        string="Total Weight (%)", 
        compute="_compute_total_weight", 
        store=True
    )
    _unique_code = models.Constraint(
    'UNIQUE(code)',
    'The Aggregate Calculation Code must be unique!'
)


    

    @api.depends('line_ids.weight')
    def _compute_total_weight(self):
        for record in self:
            record.total_weight = sum(record.line_ids.mapped('weight')) * 100

    @api.constrains('line_ids')
    def _check_duplicates(self):
        for record in self:
            entry_test_count = 0
            levels = []
            for line in record.line_ids:
                if line.source_type == 'entry_test':
                    entry_test_count += 1
                if line.source_type == 'academics' and line.academic_level_id:
                    if line.academic_level_id.id in levels:
                        raise ValidationError(_("Level %s is duplicated!") % line.academic_level_id.name)
                    levels.append(line.academic_level_id.id)
            if entry_test_count > 1:
                raise ValidationError(_("You cannot add 'Entry Test' more than once."))

    @api.constrains('total_weight')
    def _check_total_weight(self):
        for record in self:
            if record.total_weight > 100.1:
                raise ValidationError(_("Total weight cannot exceed 100%."))

class AcademyAggregateLine(models.Model):
    _name = 'academy.aggregate.line'
    _description = 'Aggregate Calculation Line'

    aggregate_id = fields.Many2one('academy.aggregate', ondelete='cascade')
    source_type = fields.Selection([
        ('entry_test', 'Entry Test'),
        ('academics', 'Academics')
    ], string="Source", required=True)
    academic_level_id = fields.Many2one('academy.level', string="Academic Level")
    
    display_weight = fields.Float(string="Weight (%)")
    weight = fields.Float(string="Weight (Stored)", digits=(16, 4), compute="_compute_weight", inverse="_inverse_weight", store=True)

    @api.depends('display_weight')
    def _compute_weight(self):
        for record in self:
            record.weight = record.display_weight / 100.0

    def _inverse_weight(self):
        for record in self:
            record.display_weight = record.weight * 100.0

    @api.onchange('source_type')
    def _onchange_source_type(self):
        if self.source_type == 'entry_test':
            self.academic_level_id = False

    @api.onchange('academic_level_id', 'source_type')
    def _set_academic_level_domain(self):
        res = {'domain': {'academic_level_id': []}}
        if self.aggregate_id:
            used_level_ids = [line.academic_level_id.id for line in self.aggregate_id.line_ids if line.academic_level_id]
            if self._origin.academic_level_id:
                used_level_ids = [l_id for l_id in used_level_ids if l_id != self._origin.academic_level_id.id]
            res['domain']['academic_level_id'] = [('id', 'not in', used_level_ids)]
        return res