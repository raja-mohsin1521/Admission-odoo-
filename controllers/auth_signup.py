import logging
from odoo import http, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_logger = logging.getLogger(__name__)

class AuthSignupHomeCustom(AuthSignupHome):

    def get_auth_signup_qcontext(self):
        """ Preserve custom fields (cnic, phone) in the signup form context """
        qcontext = super().get_auth_signup_qcontext()
        qcontext.update({
            'cnic': request.params.get('cnic'),
            'phone': request.params.get('phone'),
        })
        return qcontext

    def do_signup(self, qcontext):
        """ Complete the signup flow without crashing on Group assignment """
        
        # 1. Extract values safely
        values = {key: qcontext.get(key) for key in ('login', 'name', 'password', 'cnic', 'phone')}
        if not values.get('email'):
            values['email'] = values.get('login')

        # 2. Call Parent (This creates User AND assigns Portal Group automatically)
        super().do_signup(qcontext)

        # 3. Find the newly created user
        user = request.env['res.users'].sudo().search([('login', '=', values['login'])], limit=1)

        if user:
            # --- REMOVED THE CRASHING CODE BLOCK HERE ---
            # (We deleted the portal_group.write block entirely)

            # 4. Update User Profile (CNIC/Phone)
            # Only write if the fields actually exist on the user model
            user_updates = {}
            if 'cnic' in user._fields and values.get('cnic'):
                 user_updates['cnic'] = values.get('cnic')
            if 'phone' in user._fields and values.get('phone'):
                 user_updates['phone'] = values.get('phone')
            
            if user_updates:
                user.sudo().write(user_updates)

            # 5. Create Student Applicant Profile
            name_parts = values.get('name', '').split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            request.env['student.applicant'].sudo().create({
                'name': first_name,
                'last_name': last_name,
                'email': values['email'],
                'phone': values.get('phone'),
                'cnic': values.get('cnic'),
                'user_id': user.id,
                'state': 'registered'
            })