from odoo import models, fields, api, _, Command
from odoo.exceptions import ValidationError
import re

class StudentApplicant(models.Model):
    _name = 'student.applicant'
    _description = 'Student Registration'

    _unique_email = models.Constraint(
        'UNIQUE(email)',
        'This email is already registered!'
    )

    _unique_cnic = models.Constraint(
        'UNIQUE(cnic)',
        'A student with this CNIC already exists!'
    )

    name = fields.Char(string="First Name", required=True)
    last_name = fields.Char(string="Last Name", required=True)
    email = fields.Char(string="Email", required=True)
    phone = fields.Char(string="Phone")
    cnic = fields.Char(string="CNIC")
    applicant_type = fields.Selection([
        ('national', 'National'),
        ('international', 'International')
    ], string="Applicant Type", default='national')
    applying_for_id = fields.Many2one('academy.career', string="Applying For Career")
    user_id = fields.Many2one('res.users', string="Portal User", readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('registered', 'Registered')
    ], default='draft', string="Status")

    @api.onchange('cnic')
    def _onchange_cnic_format(self):
        if self.cnic:
            self.cnic = re.sub(r'\D', '', self.cnic)

    @api.constrains('cnic')
    def _check_cnic_format(self):
        for rec in self:
            if rec.cnic and len(rec.cnic) != 13:
                raise ValidationError(_("CNIC must be exactly 13 digits."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('cnic'):
                vals['cnic'] = re.sub(r'\D', '', vals['cnic'])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('cnic'):
            vals['cnic'] = re.sub(r'\D', '', vals['cnic'])
        return super().write(vals)

    def action_student_signup(self):
        """ Creates a Portal User for the student and links it. """
        portal_group = self.env.ref('base.group_portal')
        
        for rec in self:
            if not rec.email:
                raise ValidationError(_("Email is required."))
            
            # 1. Search for existing user
            existing_user = self.env['res.users'].sudo().search([('login', '=', rec.email)], limit=1)
            
            if not existing_user:
                # 2. Create User WITH Group (Standard Odoo Way)
                user_vals = {
                    'name': f"{rec.name} {rec.last_name}",
                    'login': rec.email,
                    'email': rec.email,
                    'groups_id': [Command.link(portal_group.id)], # Assign group directly here
                }
                existing_user = self.env['res.users'].sudo().create(user_vals)
                existing_user.action_reset_password()
            else:
                # 3. If user exists, ensure they have the group
                if portal_group not in existing_user.groups_id:
                    existing_user.sudo().write({
                        'groups_id': [Command.link(portal_group.id)]
                    })

            # 4. Link and Update Status
            rec.user_id = existing_user.id
            rec.state = 'registered'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'student.applicant',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }