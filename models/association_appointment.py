from odoo import models, fields, api

class AssociationAppointment(models.Model):
    _name = 'association.appointment'
    _description = 'Rendez-vous de l\'Association'
    _inherit = ['mail.thread'] 
    _order = 'date_start asc'

    name = fields.Char(string='Motif du Rendez-vous', required=True, placeholder="Ex: Guidance parentale, Atelier Routines...")
    
    # 🔗 Relie le RDV à la maman / l'enfant
    member_id = fields.Many2one(
        'association.beneficiary', 
        string='Maman / Bénéficiaire', 
        required=True,
        domain="[('member_type', '=', 'beneficiary')]" 
    )
    
    # 🤝 NOUVEAU : Relie le RDV au bénévole qui va l'animer
    volunteer_id = fields.Many2one(
        'association.beneficiary',
        string='Bénévole Assigné',
        domain="[('member_type', '=', 'volunteer')]"
    )
    
    date_start = fields.Datetime(string='Date et Heure de début', required=True, tracking=True)
    date_end = fields.Datetime(string='Date et Heure de fin', required=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon 📝'),
        ('confirmed', 'Confirmé 🟢'),
        ('done', 'Effectué ✅'),
        ('cancelled', 'Annulé ❌')
    ], string='Statut', default='draft', readonly=True, tracking=True)
    
    # 🌿 POUR LE JOUR-J : Permet à la maman de préparer l'accueil sur le portail web
    specific_needs_this_day = fields.Text(
        string='Besoins spécifiques pour ce RDV', 
        placeholder="Ex: Enfant très fatigué aujourd'hui, prévoir un espace très calme sans néons clignotants."
    )
    
    notes = fields.Text(string='Notes secrètes de l\'accompagnement (Bénévoles)')

        # À ajouter dans association.appointment
        # ✉️ Suivi des notifications pour éviter les oublis
    is_reminder_sent = fields.Boolean(
        string="Rappel automatique envoyé ✉️", 
        default=False, 
        readonly=True,
        tracking=True
    )
    
    # 📝 Historique clinique et éducatif (Compte-rendu)
    summary_report = fields.Text(
        string="Compte-rendu de la séance", 
        placeholder="Rédigez ici le bilan de la séance (ex: progression sur les routines, comportement face aux stimuli, points à travailler à la maison...)"
    )



    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'

    def action_done(self):
        for record in self:
            record.state = 'done'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'



        # ⏱️ Calcul automatique de la durée du rendez-vous
    duration = fields.Float(string="Durée (en heures)", compute="_compute_duration", store=True)

    # 🌈 État émotionnel / Niveau d'énergie de l'enfant signalé pour ce RDV
    child_energy_level = fields.Selection([
        ('calm', 'Calme / Réceptif 💚'),
        ('anxious', 'Anxiété / Stress 💛'),
        ('overstimulated', 'Surcharge sensorielle / Fatigué 🧡'),
        ('crisis', 'En crise / Besoin d\'espace apaisant ❤️')
    ], string="État de l'enfant ce jour", default='calm')

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for record in self:
            if record.date_start and record.date_end:
                diff = record.date_end - record.date_start
                record.duration = diff.total_seconds() / 3600.0
            else:
                record.duration = 0.0

