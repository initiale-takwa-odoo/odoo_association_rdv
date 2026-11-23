# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class AssociationContribution(models.Model):
    _name = 'association.contribution'
    _description = 'Suivi des Adhésions et Dons'
    _rec_name = 'member_id'
    _order = 'date_payment desc'

    member_id = fields.Many2one('association.beneficiary', string="Membre / Donateur", required=True)
    
    type = fields.Selection([
        ('membership', 'Cotisation Annuelle 💳'),
        ('donation', 'Don Solidaire 🎁')
    ], string="Type de transaction", required=True, default='membership')
    
    amount = fields.Float(string="Montant reçu (€)", required=True)
    date_payment = fields.Date(string="Date de réception", default=fields.Date.context_today)
    
    # 🌟 NOUVEAUX CHAMPS POUR LE REÇU FISCAL
    is_verified = fields.Boolean(string="Don vérifié par le trésorier ✅", default=False, tracking=True)
    fiscal_receipt_number = fields.Char(string="Numéro de reçu fiscal", readonly=True, copy=False)
    
    # Champ calculé pour estimer la déduction fiscale (ex: 66% en France)
    tax_deduction = fields.Float(string="Déduction d'impôt estimée (66%)", compute="_compute_tax_deduction", store=True)

    @api.depends('amount', 'type')
    def _compute_tax_deduction(self):
        for record in self:
            # Souvent, seuls les dons (et non les cotisations) ouvrent droit à réduction d'impôt
            if record.type == 'donation' and record.amount > 0:
                record.tax_deduction = record.amount * 0.66
            else:
                record.tax_deduction = 0.0

    # 🚀 ACTION DU BOUTON : Génère un numéro de reçu unique
    def action_validate_and_generate_receipt(self):
        for record in self:
            if record.amount <= 0:
                raise UserError("Le montant du don doit être supérieur à 0 € pour générer un reçu fiscal.")
            
            if not record.fiscal_receipt_number:
                current_year = record.date_payment.year if record.date_payment else datetime.now().year
                
                # Petite astuce de code pour générer un numéro unique de manière simple sans passer par les séquences lourdes d'Odoo
                # Odoo va chercher le dernier numéro de l'année en cours pour l'incrémenter
                last_receipt = self.search([
                    ('fiscal_receipt_number', 'like', f'RECU/{current_year}/')
                ], order='fiscal_receipt_number desc', limit=1)
                
                if last_receipt and last_receipt.fiscal_receipt_number:
                    last_num = int(last_receipt.fiscal_receipt_number.split('/')[-1])
                    new_num = last_num + 1
                else:
                    new_num = 1
                
                # Format final : RECU/2026/0001
                record.fiscal_receipt_number = f"RECU/{current_year}/{new_num:04d}"
            
            record.is_verified = True
