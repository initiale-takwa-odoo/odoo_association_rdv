# -*- coding: utf-8 -*-
from odoo import models, fields

class AssociationActivity(models.Model):
    _name = 'association.activity'
    _description = 'Ateliers et Activités'

    name = fields.Char(string="Nom de l'atelier", required=True, placeholder="Ex: Groupe de parole Mamans, Atelier Éveil Sensoriel")
    description = fields.Text(string="Description de l'activité")
    capacity = fields.Integer(string="Nombre de places maximum", default=10)
    
    # Liens avec nos membres existants
    beneficiary_ids = fields.Many2many(
        'association.beneficiary', 
        string="Enfants/Mamans inscrits",
        domain="[('member_type', '=', 'beneficiary')]"
    )
