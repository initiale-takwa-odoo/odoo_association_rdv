# -*- coding: utf-8 -*-
from odoo import models, fields

class AssociationChildLog(models.Model):
    _name = 'association.child.log'
    _description = "Journal de bord et Suivi de l'enfant"
    _order = 'date desc'

    # 🌟 LA LIGNE MAGIQUE : Dit à Odoo d'utiliser la date pour le titre en haut !
    _rec_name = 'date'

    # 🔗 Liaison directe avec la fiche de l'enfant
    beneficiary_id = fields.Many2one(
        'association.beneficiary', 
        string="Enfant concerné", 
        required=True,
        ondelete='cascade',
        domain="[('member_type', '=', 'beneficiary')]"
    )
    
    date = fields.Date(string="Date de l'observation", default=fields.Date.context_today, required=True)
    
    # 😴 Suivi du sommeil (Paramètre critique pour le TSA/TDAH)
    sleep_quality = fields.Selection([
        ('good', 'Sommeil réparateur / Calme 😴'),
        ('restless', 'Sommeil agité / Réveils nocturnes 🌤️'),
        ('bad', 'Nuit très difficile / Insomnie 🚨')
    ], string="Qualité du Sommeil", default='good', required=True)
    
    # 📈 Énergie globale observée
    global_anxiety = fields.Selection([
        ('low', 'Paisible / Réceptif 🟢'),
        ('medium', 'Anxiété modérée / Agité 🟡'),
        ('high', 'Forte surcharge émotionnelle 🔴')
    ], string="Niveau d'Anxiété", default='low')

    # 📝 Notes textuelles axées sur la psychologie positive
    victory_notes = fields.Text(
        string="Les victoires du jour 🎉", 
        placeholder="Ex: A réussi à finir sa routine du matin en autonomie, a verbalisé sa frustration sans s'énerver..."
    )
    challenge_notes = fields.Text(
        string="Difficultés rencontrées 🧠", 
        placeholder="Ex: Tempête émotionnelle lors du changement d'activité à 16h, hypersensibilité aux bruits du repas..."
    )
