# -*- coding: utf-8 -*-
from odoo import models, fields

class AssociationTimesheet(models.Model):
    _name = 'association.timesheet'
    _description = 'Feuilles de temps des Bénévoles'

    volunteer_id = fields.Many2one(
        'association.beneficiary', 
        string="Bénévole", 
        required=True,
        domain="[('member_type', '=', 'volunteer')]"
    )
    date = fields.Date(string="Date de l'action", default=fields.Date.context_today)
    time_spent = fields.Float(string="Temps passé (heures)", required=True, default=1.0)
    description = fields.Char(string="Action menée", required=True, placeholder="Ex: Animation groupe de parole, Tri ludothèque")
