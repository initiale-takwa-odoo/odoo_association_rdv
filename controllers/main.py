# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import http, fields
from odoo.http import request


class AssociationPortal(http.Controller):

    # =========================================================================
    # 1. TABLEAU DE BORD UNIFIÉ (MAMAN & BÉNÉVOLE)
    # =========================================================================
    @http.route(['/my/appointments'], type='http', auth='user', website=True)
    def appointment_portal_list(self, **kw):
        current_user = request.env.user
        env = request.env

        beneficiary = env['association.beneficiary'].sudo().search([
            ('user_id', '=', current_user.id)
        ], limit=1)

        is_mother = bool(beneficiary and beneficiary.member_type in ['beneficiary', 'both'])
        is_volunteer = bool(beneficiary and beneficiary.member_type in ['volunteer', 'both'])

        # Rendez-vous (Maman & Bénévole)
        appointments = env['association.appointment'].sudo().search([
            ('member_id', '=', beneficiary.id)
        ]) if beneficiary else env['association.appointment'].browse()

        volunteer_appointments = env['association.appointment'].sudo().search([
            ('volunteer_id', '=', beneficiary.id)
        ]) if is_volunteer else env['association.appointment'].browse()

        # Journal de bord de l'enfant
        journal_entries = env['association.child.log'].sudo().search([
            ('beneficiary_id', '=', beneficiary.id)
        ]) if beneficiary else env['association.child.log'].browse()

        # Ateliers & Activités
        workshops = env['association.activity'].sudo().search([])

        # Cotisations & Dons
        contributions = env['association.contribution'].sudo().search([
            ('member_id', '=', beneficiary.id)
        ]) if beneficiary else env['association.contribution'].browse()

        current_year = str(fields.Date.today().year)
        membership_active = any(
            c.type == 'membership' and c.is_verified and str(c.date_payment or '').startswith(current_year)
            for c in contributions
        )

        # Feuilles de temps (si bénévole)
        timesheets = env['association.timesheet'].sudo().search([
            ('volunteer_id', '=', beneficiary.id)
        ], order='date desc') if is_volunteer else env['association.timesheet'].browse()

        # Ludothèque (articles non mis au rebut)
        toys = env['association.resource'].sudo().search([
            ('state', '!=', 'damaged')
        ])

        values = {
            'page_name': 'my_appointments_list',
            'beneficiary': beneficiary,
            'is_mother': is_mother,
            'is_volunteer': is_volunteer,
            'appointments': appointments,
            'volunteer_appointments': volunteer_appointments,
            'journal_entries': journal_entries,
            'workshops': workshops,
            'contributions': contributions,
            'membership_active': membership_active,
            'timesheets': timesheets,
            'loan_history': beneficiary.loan_history_ids if beneficiary else [],
            'late_loans_count': beneficiary.late_loans_count if beneficiary else 0,
            'sponsored_families': beneficiary.sponsored_member_ids if is_volunteer else [],
            'toys': toys,
        }
        return request.render("odoo_association_rdv.portal_my_appointments_template", values)

    # =========================================================================
    # 2. ACTIONS LUDOTHÈQUE (EMPRUNT & RETOUR)
    # =========================================================================
    @http.route(['/my/ludotheque/borrow/<int:resource_id>'], type='http', auth='user', website=True)
    def portal_borrow_resource(self, resource_id, **kw):
        beneficiary = request.env['association.beneficiary'].sudo().search([
            ('user_id', '=', request.env.user.id)
        ], limit=1)
        resource = request.env['association.resource'].sudo().browse(resource_id)

        if beneficiary and resource.exists() and resource.state == 'available' and resource.condition != 'damaged':
            resource.write({
                'state': 'loaned',
                'current_borrower_id': beneficiary.id,
            })
            request.env['association.resource.loan.history'].sudo().create({
                'resource_id': resource.id,
                'borrower_id': beneficiary.id,
                'loan_date': fields.Date.context_today(request.env.user),
            })
        return request.redirect('/my/appointments?tab=ludotheque')

    @http.route(['/my/ludotheque/return/<int:resource_id>'], type='http', auth='user', website=True)
    def portal_return_resource(self, resource_id, **kw):
        beneficiary = request.env['association.beneficiary'].sudo().search([
            ('user_id', '=', request.env.user.id)
        ], limit=1)
        resource = request.env['association.resource'].sudo().browse(resource_id)

        if beneficiary and beneficiary.member_type in ['volunteer', 'both'] and resource.exists():
            resource.sudo().action_return_resource()
        return request.redirect('/my/appointments?tab=ludotheque')

    # =========================================================================
    # 3. ACTIONS JOURNAL DE BORD, RENDEZ-VOUS, ATELIERS & BÉNÉVOLAT
    # =========================================================================
    @http.route(['/my/journal/create'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_create_journal(self, **post):
        beneficiary_id = int(post.get('beneficiary_id', 0))
        if beneficiary_id:
            request.env['association.child.log'].sudo().create({
                'beneficiary_id': beneficiary_id,
                'date': fields.Date.context_today(request.env.user),
                'sleep_quality': post.get('sleep_quality', 'good'),
                'global_anxiety': post.get('global_anxiety', 'low'),
                'victory_notes': post.get('victory_notes'),
                'challenge_notes': post.get('challenge_notes'),
            })
        return request.redirect('/my/appointments?tab=famille')

    @http.route(['/my/workshop/join/<int:ws_id>'], type='http', auth='user', website=True)
    def portal_join_workshop(self, ws_id, **kw):
        beneficiary = request.env['association.beneficiary'].sudo().search([
            ('user_id', '=', request.env.user.id)
        ], limit=1)
        ws = request.env['association.activity'].sudo().browse(ws_id)
        if beneficiary and ws.exists():
            if len(ws.beneficiary_ids) < ws.capacity:
                ws.write({'beneficiary_ids': [(4, beneficiary.id)]})
        return request.redirect('/my/appointments?tab=famille')

    @http.route(['/my/appointment/create'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_create_appointment(self, **post):
        beneficiary = request.env['association.beneficiary'].sudo().search([
            ('user_id', '=', request.env.user.id)
        ], limit=1)

        date_str = post.get('date_start')
        if beneficiary and date_str:
            dt_start = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
            dt_end = dt_start + timedelta(hours=1)
            request.env['association.appointment'].sudo().create({
                'name': post.get('name', 'Demande de séance'),
                'member_id': beneficiary.id,
                'volunteer_id': beneficiary.sponsor_id.id if beneficiary.sponsor_id else False,
                'date_start': dt_start,
                'date_end': dt_end,
                'child_energy_level': post.get('child_energy_level', 'calm'),
                'specific_needs_this_day': post.get('specific_needs_this_day'),
                'state': 'draft',
            })
        return request.redirect('/my/appointments?tab=planning')

    @http.route(['/my/appointment/cancel/<int:app_id>'], type='http', auth='user', website=True)
    def portal_cancel_appointment(self, app_id, **kw):
        app = request.env['association.appointment'].sudo().browse(app_id)
        if app.exists() and app.member_id.user_id == request.env.user:
            app.sudo().action_cancel()
        return request.redirect('/my/appointments?tab=planning')

    @http.route(['/my/timesheet/create'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_create_timesheet(self, **post):
        beneficiary = request.env['association.beneficiary'].sudo().search([
            ('user_id', '=', request.env.user.id)
        ], limit=1)
        if beneficiary and beneficiary.member_type in ['volunteer', 'both']:
            request.env['association.timesheet'].sudo().create({
                'volunteer_id': beneficiary.id,
                'date': post.get('date') or fields.Date.context_today(request.env.user),
                'time_spent': float(post.get('time_spent', 1.0)),
                'description': post.get('description', 'Action bénévole'),
            })
        return request.redirect('/my/appointments')

    # =========================================================================
    # 4. ROUTES PUBLIQUES (ACCUEIL & INSCRIPTION)
    # =========================================================================
    @http.route(['/mon-association'], type='http', auth="public", website=True)
    def association_home(self, **kw):
        welcome_message = "Bienvenue dans votre espace solidaire. Ici, chaque enfant avance à son rythme, et chaque maman est écoutée et soutenue."
        return request.render("odoo_association_rdv.association_home_page", {'message': welcome_message})

    @http.route(['/inscription-association'], type='http', auth="public", website=True)
    def association_registration_form(self, **kw):
        return request.render("odoo_association_rdv.association_registration_template")

    # Route de traitement du formulaire d'inscription
    @http.route(['/inscription-association/submit'], type='http', auth="public", methods=['GET', 'POST'], website=True, csrf=True)
    def association_registration_submit(self, **post):
        if request.httprequest.method == 'POST' and post.get('name'):
            request.env['association.beneficiary'].sudo().create({
                'name': post.get('name'),
                'child_firstname': post.get('child_firstname'),
                'date_of_birth': post.get('date_of_birth') or False,
                'default_avatar_type': post.get('default_avatar_type', 'neutral'),
                'phone': post.get('phone'),
                'email': post.get('email'),
                'association_notes': post.get('association_notes'),
                'member_type': 'beneficiary',
                'association_category': 'handicap',
                'registration_state': 'pending', # Statut en attente de validation
            })
            return request.redirect('/inscription-association/merci')
        return request.redirect('/inscription-association')

    # Nouvelle route dédiée pour afficher la page de remerciement
    @http.route(['/inscription-association/merci'], type='http', auth="public", website=True)
    def association_registration_thanks(self, **kw):
        return request.render("odoo_association_rdv.registration_success_template")

    #Permettre à la maman d'enrichir son dossier depuis le Portail

    @http.route(['/my/profile/update'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_update_profile(self, **post):
        beneficiary = request.env['association.beneficiary'].sudo().search([
            ('user_id', '=', request.env.user.id)
        ], limit=1)
        if beneficiary:
            vals = {
                'child_firstname': post.get('child_firstname'),
                'date_of_birth': post.get('date_of_birth') or beneficiary.date_of_birth,
                'default_avatar_type': post.get('default_avatar_type', beneficiary.default_avatar_type),
                'has_sensory_sensitivity': bool(post.get('has_sensory_sensitivity')),
                'interests_or_hyperfocus': post.get('interests_or_hyperfocus'),
                'association_notes': post.get('association_notes'),
            }
            beneficiary.write(vals)
            # Déclenche le changement d'image si l'avatar a été modifié
            if 'default_avatar_type' in post:
                beneficiary._onchange_default_avatar_type()
        return request.redirect('/my/appointments?tab=famille')




