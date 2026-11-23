# -*- coding: utf-8 -*-
from odoo import models, fields, api, _ 
from odoo.exceptions import ValidationError
from datetime import timedelta

class AssociationResource(models.Model):
    _name = 'association.resource'
    _description = 'Ludothèque et Matériel Sensoriel'
    _rec_name = 'display_name'

    name = fields.Char(string="Nom du matériel", required=True, placeholder="Ex: Casque anti-bruit Maman A...")
    code = fields.Char(string="Code / N° Inventaire Unique", copy=False) 

    category = fields.Selection([
        ('toy', 'Jouet d\'éveil 🧸'),
        ('sensory', 'Matériel Sensoriel 🎧'),
        ('book', 'Livre / Guide Parent 📚')
    ], string="Catégorie", default='sensory')

    condition = fields.Selection([
        ('new', 'Neuf ✨'),
        ('good', 'Bon état 👍'),
        ('used', 'Usagé / Traces d\'usure 🩹'),
        ('damaged', 'Abîmé / À jeter ⚠️')
    ], string="État d'usure", default='good', required=True)

    current_borrower_id = fields.Many2one(
        'association.beneficiary', 
        string="Emprunteur actuel",
        domain="[('member_type', '=', 'beneficiary')]"
    )

    loan_history_ids = fields.One2many(
        'association.resource.loan.history', 
        'resource_id', 
        string="Historique des Prêts"
    )

    borrower_image = fields.Binary(related='current_borrower_id.image_128', string="Photo Emprunteur")

    
    # 1. Le champ redevient un champ standard protégé en écriture à l'écran, mais modifiable par le write
    state = fields.Selection([
        ('available', 'Disponible 🟢'),
        ('loaned', 'Prêté 📦'),
        ('damaged', 'Mis au rebut / Hors d\'usage ❌'), 
    ], string="Statut", default='available', readonly=True)

    is_current_loan_late = fields.Boolean(compute="_compute_is_current_loan_late", string="Emprunt en retard")

    @api.depends('loan_history_ids.return_date', 'loan_history_ids.due_date')
    def _compute_is_current_loan_late(self):
        today = fields.Date.context_today(self)
        for record in self:
            active_loan = record.loan_history_ids.filtered(lambda l: not l.return_date)
            if active_loan and active_loan.due_date and active_loan.due_date <= today:
                record.is_current_loan_late = True
            else:
                record.is_current_loan_late = False

    # 🤖 INTERCEPTION DE LA SAUVEGARDE AUTOMATIQUE (L'arme absolue)
    def write(self, vals):
        # Si l'utilisateur est en train de modifier l'état d'usure (condition)
        if 'condition' in vals:
            if vals.get('condition') == 'damaged':
                vals['state'] = 'damaged'
            elif vals.get('condition') in ['new', 'good', 'used']:
                # Si l'objet était mis au rebut mais qu'on le réhabilite
                for record in self:
                    if record.state == 'damaged':
                        vals['state'] = 'available'

        return super(AssociationResource, self).write(vals)


    

    def action_open_loan_wizard(self):
        self.ensure_one()
        return {
            'name': 'Attribuer un prêt 📦',
            'type': 'ir.actions.act_window',
            'res_model': 'association.resource.loan.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_resource_id': self.id}
        }

    def action_return_resource(self):
        self.ensure_one()
        active_loan = self.loan_history_ids.filtered(lambda l: not l.return_date)
        if active_loan:
            active_loan.write({'return_date': fields.Date.context_today(self)})

        self.write({
            'state': 'available',
            'current_borrower_id': False
        })

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            if record.code:
                record.display_name = f"[{record.code}] {record.name}"
            else:
                record.display_name = record.name

    @api.constrains('code')
    def _check_unique_code(self):
        for record in self:
            if record.code:
                duplicate = self.search([('code', '=', record.code), ('id', '!=', record.id)], limit=1)
                if duplicate:
                    raise ValidationError(_("Le code d'inventaire '%s' est déjà utilisé.") % record.code)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].strip()
            else:
                last_res = self.search([('code', '=like', 'MAT-%')], order='id desc', limit=1)
                if last_res and last_res.code:
                    try:
                        code_parts = last_res.code.split('-')
                        last_num = int(code_parts[1]) if len(code_parts) > 1 else 0
                        vals['code'] = f"MAT-{str(last_num + 1).zfill(4)}"
                    except (ValueError, IndexError):
                        total_mat = self.search_count([('code', '=like', 'MAT-%')])
                        vals['code'] = f"MAT-{str(total_mat + 1).zfill(4)}"
                else:
                    total_mat = self.search_count([('code', '=like', 'MAT-%')])
                    vals['code'] = f"MAT-{str(total_mat + 1).zfill(4)}"
        return super(AssociationResource, self).create(vals_list)




class AssociationResourceLoanWizard(models.TransientModel):
    _name = 'association.resource.loan.wizard'
    _description = 'Assistant de Prêt de Matériel'

    resource_id = fields.Many2one('association.resource', string="Matériel à emprunter", required=True)
    
    resource_category = fields.Selection([
        ('toy', 'Jouet d\'éveil 🧸'),
        ('sensory', 'Matériel Sensoriel 🎧'),
        ('book', 'Livre / Guide Parent 📚')
    ], related='resource_id.category', string="Catégorie Matériel", readonly=True)
    
    resource_state = fields.Selection([
        ('available', 'Disponible 🟢'),
        ('loaned', 'Prêté 📦'),
        ('damaged', 'Mis au rebut / Hors d\'usage ❌'), 
    ], related='resource_id.state', string="Statut Matériel", readonly=True)

    resource_condition = fields.Selection([
        ('new', 'Neuf ✨'),
        ('good', 'Bon état 👍'),
        ('used', 'Usagé / Traces d\'usure 🩹'),
        ('damaged', 'Abîmé / À vérifier ⚠️')
    ], related='resource_id.condition', string="État d'usure actuel", readonly=True)
    
    is_already_loaned = fields.Boolean(compute="_compute_is_already_loaned")
    borrower_id = fields.Many2one('association.beneficiary', string="Sélectionner la maman", domain="[('member_type', '=', 'beneficiary')]")

    @api.depends('resource_id', 'resource_id.state', 'resource_id.condition')
    def _compute_is_already_loaned(self):
        for wizard in self:
            if wizard.resource_id:
                wizard.is_already_loaned = (
                    wizard.resource_id.state in ['loaned', 'damaged'] or 
                    wizard.resource_id.condition == 'damaged'
                )
            else:
                wizard.is_already_loaned = False

    def action_confirm_loan(self):
        self.ensure_one()
        if self.resource_id.state in ['loaned', 'damaged'] or self.resource_id.condition == 'damaged':
            raise ValidationError(_("Sécurité : Cet article n'est pas disponible à l'emprunt !"))
        
        self.resource_id.write({
            'state': 'loaned',
            'current_borrower_id': self.borrower_id.id
        })

        self.env['association.resource.loan.history'].create({
            'resource_id': self.resource_id.id,
            'borrower_id': self.borrower_id.id,
            'loan_date': fields.Date.context_today(self),
        })
        return {'type': 'ir.actions.act_window_close'}


class AssociationResourceLoanHistory(models.Model):
    _name = 'association.resource.loan.history'
    _description = 'Historique des Prêts de Matériel'
    _order = 'loan_date desc'

    resource_id = fields.Many2one('association.resource', string="Matériel", required=True, ondelete='cascade')
    borrower_id = fields.Many2one('association.beneficiary', string="Maman / Emprunteur", required=True)
    loan_date = fields.Date(string="Date de prêt", required=True)
    return_date = fields.Date(string="Date de retour")
    borrower_image = fields.Binary(related='borrower_id.image_128', string="Photo Emprunteur", readonly=True)
    
    due_date = fields.Date(string="Date limite", compute="_compute_due_date", store=True)
    is_late = fields.Boolean(string="En retard ?", compute="_compute_is_late", search="_search_is_late")

    @api.depends('loan_date')
    def _compute_due_date(self):
        for record in self:
            if record.loan_date:
                record.due_date = record.loan_date + timedelta(days=14)
            else:
                record.due_date = False

    @api.depends('return_date', 'due_date')
    def _compute_is_late(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.return_date and record.due_date and record.due_date <= today:
                record.is_late = True
            else:
                record.is_late = False

    def _search_is_late(self, operator, value):
        today = fields.Date.context_today(self)
        if operator in ('=', '!='):
            check_late = value if operator == '=' else not value
            if check_late:
                return [('return_date', '=', False), ('due_date', '<=', today)]
            else:
                return ['|', ('return_date', '!=', False), ('due_date', '>', today)]
        return []
