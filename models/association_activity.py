# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AssociationActivity(models.Model):
    _name = 'association.activity'
    _description = 'Ateliers et Activités'
    _order = 'date_start desc, id desc'

    name = fields.Char(
        string="Nom de l'atelier", 
        required=True, 
        placeholder="Ex: Groupe de parole Mamans, Atelier Éveil Sensoriel"
    )
    description = fields.Text(string="Description de l'activité")
    
    # Dates et heures de la session
    date_start = fields.Datetime(string="Début de la session", required=True, default=fields.Datetime.now)
    date_end = fields.Datetime(string="Fin de la session")
    
    capacity = fields.Integer(string="Nombre de places maximum", default=5)
    
    # Participants confirmés
    beneficiary_ids = fields.Many2many(
        'association.beneficiary', 
        'association_activity_beneficiary_rel',
        'activity_id', 'beneficiary_id',
        string="Enfants/Mamans inscrits",
        domain="[('member_type', '=', 'beneficiary')]"
    )

    # Liste d'attente
    waitlist_ids = fields.Many2many(
        'association.beneficiary', 
        'association_activity_waitlist_rel',
        'activity_id', 'beneficiary_id',
        string="Liste d'attente",
        domain="[('member_type', '=', 'beneficiary')]"
    )

    # Compteurs
    participant_count = fields.Integer(compute='_compute_counts', string="Inscrits")
    waitlist_count = fields.Integer(compute='_compute_counts', string="En attente")

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError("La date/heure de fin ne peut pas être antérieure au début de la session.")

    @api.depends('beneficiary_ids', 'waitlist_ids')
    def _compute_counts(self):
        for rec in self:
            rec.participant_count = len(rec.beneficiary_ids)
            rec.waitlist_count = len(rec.waitlist_ids)

    @api.onchange('beneficiary_ids', 'capacity')
    def _onchange_beneficiary_ids(self):
        for rec in self:
            if rec.capacity > 0 and len(rec.beneficiary_ids) > rec.capacity:
                allowed = rec.beneficiary_ids[:rec.capacity]
                overflow = rec.beneficiary_ids[rec.capacity:]
                rec.beneficiary_ids = allowed
                rec.waitlist_ids |= overflow

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._enforce_capacity_limit()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'beneficiary_ids' in vals or 'capacity' in vals:
            self._enforce_capacity_limit()
        return res

    def _enforce_capacity_limit(self):
        for rec in self:
            if rec.capacity > 0 and len(rec.beneficiary_ids) > rec.capacity:
                allowed = rec.beneficiary_ids[:rec.capacity]
                overflow = rec.beneficiary_ids[rec.capacity:]
                rec.write({
                    'beneficiary_ids': [(6, 0, allowed.ids)],
                    'waitlist_ids': [(4, b.id) for b in overflow],
                })

    def action_promote_from_waitlist(self):
        for rec in self:
            if rec.waitlist_ids and len(rec.beneficiary_ids) < rec.capacity:
                first_in_line = rec.waitlist_ids[0]
                rec.waitlist_ids -= first_in_line
                rec.beneficiary_ids |= first_in_line
