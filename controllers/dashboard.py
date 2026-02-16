from odoo import http
from odoo.http import request
import json

class AcademyDashboard(http.Controller):

    def _get_base_domain(self, date_from=None, date_to=None, register_id=None, register_type=None):
        domain = []
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))
            
        if register_id and register_id != 'all':
            try:
                domain.append(('register_id', '=', int(register_id)))
            except ValueError:
                pass
                
        if register_type == 'active':
            domain.append(('register_id.state', 'in', ['gathering','stopped', 'merit']))
            
        return domain

    @http.route('/academy/dashboard/stats', type='json', auth='user')
    def get_stats(self, date_from=None, date_to=None, register_id=None, register_type=None):
        App = request.env['student.application'].sudo()
        domain = self._get_base_domain(date_from, date_to, register_id, register_type)

        def count(field, value):
            return App.search_count(domain + [(field, '=', value)])

        registers = request.env['admission.register'].sudo().search([])
        register_list = [{"id": r.id, "name": r.name} for r in registers]

        total = App.search_count(domain)
        male = App.search_count(domain + [('gender', '=', 'male')])
        female = App.search_count(domain + [('gender', '=', 'female')])
        other = App.search_count(domain + [('gender', '=', 'other')])

        records = App.search(domain)
        aggregates = records.mapped('aggregate_score')
        avg_aggregate = sum(aggregates) / len(aggregates) if aggregates else 0.0
        highest_aggregate = max(aggregates) if aggregates else 0.0

        return {
            "registers": register_list,
            "total_stats": {
                "total": total,
                "male": male,
                "female": female,
                "other": other,
                "avg_aggregate": round(avg_aggregate, 2),
                "highest_aggregate": round(highest_aggregate, 2),
            },
            "app": [
                {"key": "draft", "title": "Draft", "value": count('state', 'draft')},
                {"key": "submit", "title": "Submitted", "value": count('state', 'submit')},
                {"key": "voucher_uploaded", "title": "Voucher Uploaded", "value": count('state', 'voucher_uploaded')},
                {"key": "approve", "title": "Approved", "value": count('state', 'approve')},
                {"key": "done", "title": "Done", "value": count('state', 'done')},
                {"key": "cancel", "title": "Cancelled", "value": count('state', 'cancel')},
            ],
            "voucher": [
                {"key": "draft", "title": "Draft", "value": count('voucher_state', 'draft')},
                {"key": "downloaded", "title": "Downloaded", "value": count('voucher_state', 'downloaded')},
                {"key": "uploaded", "title": "Uploaded", "value": count('voucher_state', 'uploaded')},
                {"key": "verified", "title": "Verified", "value": count('voucher_state', 'verified')},
                {"key": "rejected", "title": "Rejected", "value": count('voucher_state', 'rejected')},
            ]
        }

    @http.route('/academy/dashboard/filter', type='http', auth='user')
    def filter_applications(self, field=None, value=None, date_from=None, date_to=None, register_id=None):
        allowed_fields = ['state', 'voucher_state', 'gender']
        if field not in allowed_fields:
            return request.redirect('/academy/dashboard')

        action = request.env.ref('odoo19_academy.action_student_application').sudo().read()[0]
        domain = [(field, '=', value)]
        
        if register_id and register_id != 'all':
            try:
                domain.append(('register_id', '=', int(register_id)))
            except ValueError:
                pass
        
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))

        url = "/web#action=%s&model=student.application&view_type=list&domain=%s" % (
            action['id'],
            json.dumps(domain)
        )
        return request.redirect(url)

    @http.route('/academy/dashboard', type='http', auth='user')
    def dashboard(self, **kwargs):
        return request.render('odoo19_academy.academy_dashboard_template')