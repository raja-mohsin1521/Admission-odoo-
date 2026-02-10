from venv import logger
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import json
import base64

class AcademyAuthSignup(AuthSignupHome):
    def _login_redirect(self, uid, redirect=None):
        app_count = request.env['student.application'].sudo().search_count([('applicant_id.user_id', '=', uid)])
        if app_count == 0:
            return '/my/applications/new'
        return super()._login_redirect(uid, redirect=redirect)

class StudentPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'application_count' in counters:
            values['application_count'] = request.env['student.application'].sudo().search_count([
                ('applicant_id.user_id', '=', request.env.user.id)
            ])
        return values

    @http.route(['/my/applications', '/my/applications/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_applications(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        domain = [('applicant_id.user_id', '=', user.id)]
        
        app_count = request.env['student.application'].sudo().search_count(domain)
        pager = portal_pager(
            url="/my/applications",
            total=app_count,
            page=page,
            step=10
        )
        apps = request.env['student.application'].sudo().search(
            domain, 
            limit=10, 
            offset=pager['offset'], 
            order='create_date desc'
        )
        values.update({
            'applications': apps,
            'page_name': 'student_application',
            'pager': pager,
            'default_url': '/my/applications',
            'application_count': app_count,
        })
        return request.render("odoo19_academy.portal_my_applications", values)

    @http.route(['/my/applications/new'], type='http', auth="user", website=True)
    def portal_new_application(self, **kw):
        registers = request.env['admission.register'].sudo().search([('state', '=', 'gathering')])
        existing = request.env['student.application'].sudo().search([('applicant_id.user_id', '=', request.env.user.id)])
        return request.render("odoo19_academy.select_admission_register", {
            'registers': registers,
            'applied_register_ids': existing.mapped('register_id.id'),
            'existing_apps': {app.register_id.id: app.id for app in existing},
            'page_name': 'new_application',
        })

    @http.route(['/admission/register/select'], type='http', auth="user", methods=['POST'], website=True)
    def select_register_confirm(self, register_id, **kw):
        user = request.env.user
        register = request.env['admission.register'].sudo().browse(int(register_id))
        
        applicant = request.env['student.applicant'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not applicant:
            name_parts = user.name.split(" ", 1)
            applicant = request.env['student.applicant'].sudo().create({
                'name': name_parts[0],
                'last_name': name_parts[1] if len(name_parts) > 1 else "",
                'email': user.email,
                'phone': user.phone,
                'cnic': user.cnic,
                'user_id': user.id,
                'partner_id': user.partner_id.id
            })

        app = request.env['student.application'].sudo().search([
            ('applicant_id', '=', applicant.id),
            ('register_id', '=', register.id)
        ], limit=1)

        if not app:
            app = request.env['student.application'].sudo().create({
                'applicant_id': applicant.id,
                'register_id': register.id,
                'cnic': applicant.cnic,
                'email': applicant.email or user.email,
                'phone': applicant.phone or user.phone,
                'academic_session_id': register.academic_session_id.id,
                'academic_term_id': register.academic_term_id.id,
            })
        return request.redirect(f'/my/application/{app.id}')

    @http.route(['/my/application/<model("student.application"):application>'], type='http', auth="user", website=True)
    def portal_my_application_detail(self, application, **kw):
        if application.applicant_id.user_id != request.env.user:
            return request.redirect('/my/applications')

        step = 1
        if application.father_name and application.father_cnic:
            step = 2
            if application.dob and application.gender and application.province:
                step = 3
                if application.education_line_ids:
                    step = 4
                    if application.preference_line_ids:
                        step = 5

        levels = request.env['academy.level'].sudo().search([])
        degrees = request.env['academy.degree'].sudo().search([])
        specializations = request.env['academy.specialization'].sudo().search([])
        countries = request.env['res.country'].sudo().search([])
        eligible_programs = self._get_eligible_programs(application)

        return request.render("odoo19_academy.portal_my_application_detail", {
            'application': application,
            'countries': countries,
            'levels': levels,
            'degrees': degrees,
            'specializations': specializations,
            'eligible_programs': eligible_programs,
            'offered_programs': application.register_id.program_ids,
            'page_name': 'student_application',
            'current_step': step,
            'error': kw.get('error'),
            'success': kw.get('success'),
        })
    
    def _get_eligible_programs(self, application):
        """
        Filters programs based on AcademyProgramEligibility rules.
        """
        # If no education entered yet, show everything (or nothing, depending on UX preference)
        if not application.education_line_ids:
            return application.register_id.program_ids
        
        eligible_program_ids = set()
        
        # Optimize: Fetch only rules related to the student's degrees
        student_degree_ids = application.education_line_ids.mapped('academic_degree_id').ids
        relevant_rules = request.env['academy.program.eligibility'].sudo().search([
            ('degree_id', 'in', student_degree_ids)
        ])
        
        for edu in application.education_line_ids:
            # Filter rules for this specific education line's degree
            matching_rules = relevant_rules.filtered(lambda r: r.degree_id.id == edu.academic_degree_id.id)
            
            for rule in matching_rules:
                # 1. Check Specialization
                # If rule has specializations, student MUST match one of them.
                # If rule has NO specializations, it applies to all.
                if rule.specialization_ids:
                    if not edu.specialization_id or edu.specialization_id.id not in rule.specialization_ids.ids:
                        continue # Skip this rule, specialization doesn't match

                # 2. Check Scores based on Evaluation Type
                score_eligible = False
                
                if rule.evaluation_type == 'percentage':
                    # Standard Percentage Check
                    if rule.eligibility_percentage_min <= edu.percentage <= rule.eligibility_percentage_max:
                        score_eligible = True
                
                elif rule.evaluation_type == 'cgpa':
                    # CGPA Check
                    # Assumption: If total marks is small (<= 5.0), the obtained_marks IS the CGPA.
                    # If total marks is large (e.g. 1100), it's not CGPA, so this rule fails/skips.
                    if edu.total_marks <= 5.0: 
                        if rule.eligibility_cgpa_min <= edu.obtained_marks <= rule.eligibility_cgpa_max:
                            score_eligible = True
                
                if score_eligible:
                    eligible_program_ids.update(rule.program_ids.ids)
        
        # Intersect eligible programs with what is currently offered in the register
        offered_programs_ids = set(application.register_id.program_ids.ids)
        final_ids = list(eligible_program_ids & offered_programs_ids)
        
        # If user has education but matches NOTHING, they get an empty list (not all programs)
        return request.env['academy.program'].sudo().browse(final_ids)

    @http.route(['/my/application/save'], type='http', auth="user", methods=['POST'], website=True)
    def portal_application_save(self, application_id, **kw):
        app = request.env['student.application'].sudo().browse(int(application_id))
        if app.applicant_id.user_id != request.env.user:
            return request.redirect('/my/applications')

        submit_stage = kw.get('submit_stage')
        
        try:
            if submit_stage == 'personal':
                personal_vals = {
                    'father_name': kw.get('father_name', '').strip(),
                    'father_cnic': kw.get('father_cnic', '').strip(),
                    'father_status': kw.get('father_status', '').strip(),
                    'mother_name': kw.get('mother_name', '').strip(),
                    'mother_cnic': kw.get('mother_cnic', '').strip(),
                    'mother_status': kw.get('mother_status', '').strip(),
                    'mother_cell': kw.get('mother_cell', '').strip(),
                    'mother_education': kw.get('mother_education', '').strip(),
                    'mother_profession': kw.get('mother_profession', '').strip(),
                    'guardian_name': kw.get('guardian_name', '').strip(),
                    'guardian_relation': kw.get('guardian_relation', '').strip(),
                    'guardian_cnic': kw.get('guardian_cnic', '').strip(),
                    'guardian_cell': kw.get('guardian_cell', '').strip(),
                    'guardian_income': float(kw.get('guardian_income') or 0.0),
                    'guardian_address': kw.get('guardian_address', '').strip(),
                }
                if not personal_vals['father_name'] or not personal_vals['father_cnic'] or not personal_vals['guardian_name']:
                    return request.redirect(f'/my/application/{app.id}?error=Father and Guardian Name/CNIC are required.')
                student_image = kw.get('image_1920')
                if student_image:
                    personal_vals['image_1920'] = base64.b64encode(student_image.read())
                
                app.sudo().write(personal_vals)
                return request.redirect(f'/my/application/{app.id}?success=Personal Info Saved. Proceed to Demographics.')

            if submit_stage == 'demographics':
                demo_vals = {
                    'dob': kw.get('dob', '').strip() or False,
                    'gender': kw.get('gender', '').strip(),
                    'religion': kw.get('religion', '').strip(),
                    'blood_group': kw.get('blood_group', '').strip(),
                    'nationality_id': int(kw.get('nationality_id')) if kw.get('nationality_id') else False,
                    'passport': kw.get('passport', '').strip(),
                    'province': kw.get('province', '').strip(),
                    'domicile': kw.get('domicile', '').strip(),
                    'present_address': kw.get('present_address', '').strip(),
                    'how_did_you_know': kw.get('how_did_you_know', '').strip(),
                }
                if not demo_vals['dob'] or not demo_vals['gender'] or not demo_vals['province']:
                    return request.redirect(f'/my/application/{app.id}?error=DOB, Gender and Province are required.')

                app.sudo().write(demo_vals)
                return request.redirect(f'/my/application/{app.id}?success=Demographics Saved. Proceed to Education.')

            if submit_stage == 'education':
                app.education_line_ids.sudo().unlink()
                education_index = 0
                has_education = False
                while True:
                    level_key = f'education[{education_index}][level_id]'
                    if level_key not in kw and education_index > 20:
                        break
                    
                    if level_key in kw:
                        level_id = kw.get(level_key)
                        degree_id = kw.get(f'education[{education_index}][degree_id]')
                        specialization_id = kw.get(f'education[{education_index}][specialization_id]')
                        total_marks = float(kw.get(f'education[{education_index}][total_marks]', 0))
                        obtained_marks = float(kw.get(f'education[{education_index}][obtained_marks]', 0))
                        
                        if level_id and degree_id and total_marks > 0:
                            if obtained_marks > total_marks:
                                return request.redirect(f'/my/application/{app.id}?error=Obtained marks cannot be greater than total marks.')
                            
                            education_vals = {
                                'application_id': app.id,
                                'academic_level_id': int(level_id),
                                'academic_degree_id': int(degree_id),
                                'specialization_id': int(specialization_id) if specialization_id else False,
                                'total_marks': total_marks,
                                'obtained_marks': obtained_marks,
                            }
                            request.env['student.application.education'].sudo().create(education_vals)
                            has_education = True
                    
                    education_index += 1

                if not has_education:
                    return request.redirect(f'/my/application/{app.id}?error=Please add at least one educational qualification.')
                
                return request.redirect(f'/my/application/{app.id}?success=Education Saved. Proceed to Preferences.')

            if submit_stage == 'preferences':
                app.preference_line_ids.sudo().unlink()
                has_pref = False
                for i in range(1, 4):
                    prog_id = kw.get(f'pref_{i}')
                    if prog_id:
                        preference_vals = {
                            'application_id': app.id,
                            'preference_no': i,
                            'program_id': int(prog_id)
                        }
                        request.env['student.application.preference'].sudo().create(preference_vals)
                        has_pref = True
                
                if not has_pref:
                    return request.redirect(f'/my/application/{app.id}?error=Please select at least one program preference.')

                return request.redirect(f'/my/application/{app.id}?success=Preferences Saved. Ready to Submit.')

            if submit_stage == 'final':
                errors = []
                if not app.father_name: errors.append("Personal Info incomplete")
                if not app.dob: errors.append("Demographics incomplete")
                if not app.education_line_ids: errors.append("Education incomplete")
                if not app.preference_line_ids: errors.append("Preferences incomplete")
                
                if errors:
                    return request.redirect(f'/my/application/{app.id}?error={", ".join(errors)}')
                
                app.sudo().action_submit()
                return request.redirect('/my/applications?success=Application+submitted+successfully')
            
            return request.redirect(f'/my/application/{app.id}')

        except Exception as e:
            return request.redirect(f'/my/application/{app.id}?error={str(e)}')

    @http.route(['/my/application/check_eligibility'], type='http', auth="user", website=True)
    def check_program_eligibility(self, application_id, program_id, **kw):
        try:
            app = request.env['student.application'].sudo().browse(int(application_id))
            program = request.env['academy.program'].sudo().browse(int(program_id))
            
            if not app or not program:
                return json.dumps({'eligible': False, 'message': 'Invalid data'})
            
            eligible = False
            requirements = []
            
            # Find rules associated with the specific program being checked
            rules = request.env['academy.program.eligibility'].sudo().search([
                ('program_ids', 'in', program.id)
            ])
            
            if not rules:
                # If no rules exist for a program, is it open to all? 
                # Assuming restricted by default if criteria exists elsewhere.
                return json.dumps({'eligible': False, 'message': 'No eligibility criteria defined for this program.'})

            for rule in rules:
                # Build requirement text based on Evaluation Type
                req_text = f"{rule.degree_id.name}"
                
                if rule.evaluation_type == 'percentage':
                    req_text += f" (Min {rule.eligibility_percentage_min}%)"
                elif rule.evaluation_type == 'cgpa':
                    req_text += f" (Min CGPA {rule.eligibility_cgpa_min})"
                    
                if rule.specialization_ids:
                    req_text += f" in {', '.join(rule.specialization_ids.mapped('name'))}"
                
                requirements.append(req_text)
                
                # Check against Student Education Lines
                for edu in app.education_line_ids:
                    if edu.academic_degree_id == rule.degree_id:
                        
                        # Specialization Check
                        if rule.specialization_ids:
                            if not edu.specialization_id or edu.specialization_id.id not in rule.specialization_ids.ids:
                                continue

                        # Score Check
                        if rule.evaluation_type == 'percentage':
                            if rule.eligibility_percentage_min <= edu.percentage <= rule.eligibility_percentage_max:
                                eligible = True
                                break
                        elif rule.evaluation_type == 'cgpa':
                            if edu.total_marks <= 5.0: # Ensure it is a CGPA scale input
                                if rule.eligibility_cgpa_min <= edu.obtained_marks <= rule.eligibility_cgpa_max:
                                    eligible = True
                                    break
                
                if eligible:
                    break
            
            if eligible:
                return json.dumps({'eligible': True, 'message': 'You are eligible for this program'})
            else:
                return json.dumps({'eligible': False, 'message': f"You are not eligible for {program.name}. Requirements:\n" + "\n".join(requirements)})
                
        except Exception as e:
            return json.dumps({'eligible': False, 'message': str(e)})

    # --- NEW VOUCHER ROUTES ---

    @http.route(['/my/application/download_voucher/<model("student.application"):application>'], type='http', auth="user", website=True)
    def download_fee_voucher(self, application, **kw):
        """Generates the PDF for the Fee Voucher report"""
        if application.applicant_id.user_id != request.env.user:
            return request.redirect('/my/applications')
        
        report_action = 'odoo19_academy.report_fee_voucher_action'
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(report_action, [application.id])
        
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', f'attachment; filename=Fee_Voucher_{application.id}.pdf;')
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(['/my/application/voucher/upload'], type='http', auth="user", methods=['POST'], website=True)
    def portal_voucher_upload(self, application_id, **kw):
        """Saves the uploaded voucher image, payer name, and moves state forward"""
        print("Incoming Voucher Data:", kw) 
        
        app = request.env['student.application'].sudo().browse(int(application_id))
        if not app.exists() or app.applicant_id.user_id != request.env.user:
            return request.redirect('/my/applications')

        voucher_image = kw.get('voucher_image')
        voucher_number = kw.get('voucher_number')
        voucher_amount = kw.get('voucher_amount')
        fee_submit_date = kw.get('fee_submit_date')

        if not voucher_image:
            return request.redirect(f'/my/application/{app.id}?error=Voucher image is missing.')

        try:
            vals = {
                'voucher_number': voucher_number,
                'voucher_amount': voucher_amount,
                'fee_submit_date': fee_submit_date or fields.Date.today(),
                'voucher_state': 'uploaded',
                'state': 'voucher_uploaded'
            }

            if voucher_image:
                file_content = voucher_image.read()
                vals['voucher_image'] = base64.b64encode(file_content)

            app.sudo().write(vals)
            
            return request.redirect(f'/my/application/{app.id}?success=Voucher submitted successfully.')
            
        except Exception as e:
            logger.error("Voucher Upload Error: %s", str(e))
            return request.redirect(f'/my/application/{app.id}?error=System error during upload.')
        
   
    @http.route(['/my/application/test_slot/confirm'], type='http', auth="user", methods=['POST'], website=True)
    def portal_confirm_test_slot(self, application_id, **kw):
        app = request.env['student.application'].sudo().browse(int(application_id))
        if not app.exists() or app.applicant_id.user_id != request.env.user:
            return request.redirect('/my/applications')

        try:
            app.sudo().write({
                'test_type_id': int(kw.get('test_type_id')) if kw.get('test_type_id') else False,
                'test_center_id': int(kw.get('test_center_id')) if kw.get('test_center_id') else False,
                'test_slot_id': int(kw.get('test_slot_id')) if kw.get('test_slot_id') else False,
                'confirm_test_slot': True,
                'state': 'approve'
            })
            return request.redirect('/my/applications?success=Slot Confirmed and Approved')
        except Exception as e:
            return request.redirect(f'/my/application/{app.id}?error={str(e)}')