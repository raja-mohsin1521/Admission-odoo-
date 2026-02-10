from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
class StudentApplication(models.Model):
    _name = 'student.application'
    _description = 'Student Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Application No", readonly=True, default="New", copy=False)
    image_1920 = fields.Image(string="Student Image")
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('voucher_uploaded', 'Voucher Uploaded'),
        ('approve', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    applicant_id = fields.Many2one('student.applicant', string="Student", required=True)
    cnic = fields.Char(string="CNIC", readonly=True)
    email = fields.Char(string="Email", readonly=True)
    phone = fields.Char(string="Mobile")
    
    register_id = fields.Many2one(
        'admission.register', 
        string="Admission Register", 
        required=True, 
        domain=[('state', '=', 'gathering')]
    )
    academic_session_id = fields.Many2one('academy.academic.session', string="Academic Session", required=True)
    academic_term_id = fields.Many2one('academy.term.scheme', string="Academic Term" , required=True)
    test_score = fields.Float(string="Test Score", compute='_compute_test_score', store=True, readonly=True)

    voucher_number = fields.Char(string="Voucher Number")
    fee_submit_date = fields.Date(string="Fee Submit Date")
    voucher_verified_date = fields.Date(string="Voucher Verified Date")
    voucher_issue_date = fields.Date(string="Voucher Issue Date")
    
    voucher_state = fields.Selection([
        ('draft', 'Draft'),
        ('downloaded', 'Downloaded'),
        ('uploaded', 'Uploaded'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], string="Fee Voucher State", default='draft', tracking=True)
    
    voucher_amount = fields.Float(string="Amount", default=0.0)
    voucher_image = fields.Binary(string="Voucher Copy")

    test_type_id = fields.Many2one('academy.test.type', string="Test Type")
    test_center_id = fields.Many2one('academy.test.center', string="Test Center")
    test_slot_id = fields.Many2one(
        'academy.test.timing', 
        string="Test Slot",
        domain="[('center_id', '=', test_center_id), ('active', '=', True)]"
    )
    confirm_test_slot = fields.Boolean(string="Confirm Test Slot", default=False)

    education_line_ids = fields.One2many('student.application.education', 'application_id', string="Education Details", required=True)
    preference_line_ids = fields.One2many('student.application.preference', 'application_id', string="Program Preferences", required=True)

    father_name = fields.Char(string="Father Name")
    father_cnic = fields.Char(string="Father CNIC")
    father_status = fields.Selection([('alive', 'Alive'), ('deceased', 'Deceased')], string="Father Status")
    
    mother_name = fields.Char(string="Mother Name")
    mother_cnic = fields.Char(string="Mother CNIC")
    mother_status = fields.Selection([('alive', 'Alive'), ('deceased', 'Deceased')], string="Mother Status")
    mother_cell = fields.Char(string="Mother Cell")
    mother_education = fields.Char(string="Mother Education")
    mother_profession = fields.Char(string="Mother Profession")
    
    guardian_name = fields.Char(string="Guardian Name")
    guardian_relation = fields.Char(string="Relation")
    guardian_cnic = fields.Char(string="Guardian CNIC")
    guardian_cell = fields.Char(string="Guardian Cell")
    guardian_income = fields.Float(string="Monthly Income")
    guardian_address = fields.Text(string="Address")

    dob = fields.Date(string="Date of Birth")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], string="Gender")
    religion = fields.Char(string="Religion")
    blood_group = fields.Char(string="Blood Group")
    nationality_id = fields.Many2one('res.country', string="Nationality")
    passport = fields.Char(string="Passport/ID")
    province = fields.Char(string="Province")
    domicile = fields.Char(string="Domicile")
    present_address = fields.Text(string="Present Address")
    how_did_you_know = fields.Char(string="How did you know about us?")
    aggregate_score = fields.Float(string="Aggregate Score", compute="_compute_aggregate_score", store=True)
    
    

    @api.depends('test_score_ids.percentage', 'education_line_ids.percentage', 'register_id.calculation_method')
    def _compute_aggregate_score(self):
        for rec in self:
            total = 0.0
            formula = rec.register_id.calculation_method
            
            # Log the start of computation for this specific application
            _logger.info("--- Computing Aggregate for Application: %s ---", rec.name)
            
            if formula:
                _logger.info("Using Formula: %s", formula.name)
                for line in formula.line_ids:
                    line_contribution = 0.0
                    
                    if line.source_type == 'entry_test':
                        test_rec = rec.test_score_ids[:1]
                        test_perc = test_rec.percentage if test_rec else 0.0
                        line_contribution = test_perc * line.weight
                        total += line_contribution
                        _logger.info("[Entry Test] Perc: %s * Weight: %s = %s", test_perc, line.weight, line_contribution)
                    
                    elif line.source_type == 'academics' and line.academic_level_id:
                        matching_edu = rec.education_line_ids.filtered(
                            lambda e: e.academic_level_id.id == line.academic_level_id.id
                        )
                        if matching_edu:
                            edu_perc = max(matching_edu.mapped('percentage') or [0.0])
                            line_contribution = edu_perc * line.weight
                            total += line_contribution
                            _logger.info("[Academic: %s] Perc: %s * Weight: %s = %s", 
                                        line.academic_level_id.name, edu_perc, line.weight, line_contribution)
                        else:
                            _logger.warning("[Academic: %s] No matching education record found!", line.academic_level_id.name)
            
            rec.aggregate_score = total
            _logger.info(">>> Final Aggregate Score: %s", total)
                

    @api.onchange('applicant_id')
    def _onchange_applicant_id(self):
        if self.applicant_id:
            self.cnic = self.applicant_id.cnic
            self.email = self.applicant_id.email
            self.phone = self.applicant_id.phone

    @api.onchange('register_id')
    def _onchange_register_id(self):
        if self.register_id:
            self.academic_session_id = self.register_id.academic_session_id
            self.academic_term_id = self.register_id.academic_term_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('student.application') or 'New'
        return super(StudentApplication, self).create(vals_list)
    
    @api.depends('test_score_ids.obtained_marks')
    def _compute_test_score(self):
        for rec in self:
            score = rec.test_score_ids[:1]
            rec.test_score = score.obtained_marks if score else 0.0

    def action_submit(self): 
        self.write({'state': 'submit'})

    def action_voucher_uploaded(self):
        if not self.voucher_image:
            raise ValidationError(_("Please upload the voucher image before proceeding."))
        self.write({
            'state': 'voucher_uploaded',
            'voucher_state': 'uploaded'
        })

    def action_approve(self): 
        if self.voucher_state != 'verified':
            raise ValidationError(_("Application cannot be approved until the fee voucher is in 'Verified' state."))
        self.write({'state': 'approve'})

    def action_done(self): 
        self.write({'state': 'done'})

    def action_draft(self): 
        self.write({'state': 'draft'})

    def action_cancel(self): 
        self.write({'state': 'cancel'})

    def action_verify_voucher(self):
        self.write({
            'voucher_state': 'verified',
            'voucher_verified_date': fields.Date.today()
        })

    def action_reject_voucher(self):
        self.write({'voucher_state': 'rejected'})

    def action_approve(self): 
        if self.voucher_state != 'verified':
            raise ValidationError(_("Application cannot be approved until the fee voucher is in 'Verified' state."))
        
        # Original state transition
        self.write({'state': 'approve'})

        # Automatic Creation of Test Score Entry
        for rec in self:
            # Check if a score record already exists for this application
            existing_score = self.env['admission.test.score'].search([
                ('application_id', '=', rec.id)
            ], limit=1)
            
            if not existing_score:
                self.env['admission.test.score'].create({
                    'application_id': rec.id,
                    'obtained_marks': 0.0,
                    'max_marks': 100.0,
                })
                _logger.info("Test Score record created for Application: %s", rec.name)
                
                
   
    def write(self, vals):
        # 1. Allow the change to happen first (Standard Odoo behavior)
        res = super(StudentApplication, self).write(vals)

        # 2. Check if the 'state' is being changed to 'approve'
        if vals.get('state') == 'approve':
            
            # 3. Loop through records to create scores
            for rec in self:
                # Safety: Check if score already exists (to prevent duplicates)
                existing_score = self.env['admission.test.score'].sudo().search([
                    ('application_id', '=', rec.id)
                ], limit=1)
                
                if not existing_score:
                    # Create the score record
                    self.env['admission.test.score'].sudo().create({
                        'application_id': rec.id,
                        'obtained_marks': 0.0,
                        'max_marks': 100.0,
                    })
                    
        return res

class StudentEducation(models.Model):
    _name = 'student.application.education'
    _description = 'Education Lines'

    application_id = fields.Many2one('student.application', ondelete='cascade')
    academic_level_id = fields.Many2one('academy.level', string="Level", required=True)
    academic_degree_id = fields.Many2one('academy.degree', string="Degree", required=True)
    specialization_id = fields.Many2one('academy.specialization', string="Specialization")
    total_marks = fields.Float(string="Total")
    obtained_marks = fields.Float(string="Obtained")
    percentage = fields.Float(string="Percentage", compute="_compute_pc", store=True)
    

    @api.depends('total_marks', 'obtained_marks')
    def _compute_pc(self):
        for rec in self:
            rec.percentage = (rec.obtained_marks / rec.total_marks * 100) if rec.total_marks > 0 else 0.0

    @api.onchange('academic_level_id')
    def _onchange_academic_level_id(self):
        self.academic_degree_id = False
        self.specialization_id = False
        return {
            'domain': {
                'academic_degree_id': [('level_id', '=', self.academic_level_id.id)]
            }
        }

    @api.onchange('academic_degree_id')
    def _onchange_academic_degree_id(self):
        self.specialization_id = False
        return {
            'domain': {
                'specialization_id': [('degree_id', '=', self.academic_degree_id.id)]
            }
        }

    @api.constrains('academic_level_id', 'academic_degree_id')
    def _check_degree_level(self):
        for rec in self:
            if rec.academic_degree_id and rec.academic_degree_id.level_id != rec.academic_level_id:
                raise ValidationError("Selected Degree does not belong to the selected Academic Level.")

    @api.constrains('academic_degree_id', 'specialization_id')
    def _check_specialization_degree(self):
        for rec in self:
            if rec.specialization_id and rec.specialization_id.degree_id != rec.academic_degree_id:
                raise ValidationError("Selected Specialization does not belong to the selected Degree.")


class StudentPreference(models.Model):
    _name = 'student.application.preference'
    _description = 'Program Preferences'
    _order = 'preference_no'

    application_id = fields.Many2one('student.application', ondelete='cascade')
    preference_no = fields.Integer(string="Preference No", required=True)
    program_id = fields.Many2one('academy.program', string="Program", required=True)

    @api.onchange('application_id', 'application_id.register_id', 'application_id.education_line_ids')
    def _onchange_program_id_domain(self):
        if not self.application_id or not self.application_id.register_id:
            self.program_id = False
            return {'domain': {'program_id': [('id', 'in', [])]}}

        offered_programs = self.application_id.register_id.program_ids
        eligible_program_ids = set()

        for edu in self.application_id.education_line_ids:
            if not edu.academic_degree_id:
                continue

            criteria = self.env['academy.program.eligibility'].search([
                ('degree_id', '=', edu.academic_degree_id.id),
                ('eligibility_percentage_min', '<=', edu.percentage),
                ('eligibility_percentage_max', '>=', edu.percentage)
         ])

        for rule in criteria:
            if not rule.specialization_ids or (
                edu.specialization_id and edu.specialization_id.id in rule.specialization_ids.ids
            ):
                eligible_program_ids.update(rule.program_ids.ids)

        final_ids = list(set(offered_programs.ids) & eligible_program_ids)

        self.program_id = False

        if not final_ids:
            return {'domain': {'program_id': [('id', 'in', [])]}}

        return {'domain': {'program_id': [('id', 'in', final_ids)]}}

    @api.constrains('program_id')
    def _check_eligibility(self):
        for rec in self:
            if not rec.application_id.register_id:
                raise ValidationError(_("Please select an Admission Register first."))

            if rec.program_id not in rec.application_id.register_id.program_ids:
                raise ValidationError(_("The program '%s' is not offered in the selected Admission Register (%s).") % (
                    rec.program_id.name, rec.application_id.register_id.name))

            eligible_rules = self.env['academy.program.eligibility'].search([
                ('program_ids', 'in', rec.program_id.id)
            ])
            
            if not eligible_rules:
                continue

            is_eligible = False
            requirement_details = []
            
            for rule in eligible_rules:
                requirement_details.append(_("- %s: Min %s%%") % (rule.degree_id.name, rule.eligibility_percentage_min))
                
                for edu in rec.application_id.education_line_ids:
                    if edu.academic_degree_id == rule.degree_id:
                        if rule.eligibility_percentage_min <= edu.percentage <= rule.eligibility_percentage_max:
                            if not rule.specialization_ids or (edu.specialization_id and edu.specialization_id.id in rule.specialization_ids.ids):
                                is_eligible = True
                                break
                if is_eligible:
                    break

            if not is_eligible:
                msg = _("You are not eligible for '%s'. Minimum criteria for this program:\n%s") % (
                    rec.program_id.name, "\n".join(requirement_details))
                raise ValidationError(msg)