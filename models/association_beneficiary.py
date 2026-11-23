import base64
from datetime import date
from pathlib import Path  # 🌟 Indispensable pour calculer les chemins sous Odoo 19
from odoo import models, fields, api


class AssociationBeneficiary(models.Model):
    _name = 'association.beneficiary'
    # 🌟 AJOUT DE L'HÉRITAGE DES MODULES DE MESSAGERIE D'ODOO
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Obligatoire pour le chatter
    _description = "Membres de l'Association"
    _order = 'name asc'

    

    name = fields.Char(string="Nom de famille de la Maman", required=True)
    child_firstname = fields.Char(string="Prénom de l'enfant")
    # 📸 Le champ image officiel (Odoo va créer automatiquement une version redimensionnée en 128x128)
    image_128 = fields.Image(string="Photo du membre / Enfant", max_width=128, max_height=128)

    date_of_birth = fields.Date(string="Date de naissance de l'enfant")
    age = fields.Integer(string="Âge de l'enfant", compute="_compute_age", store=True)
    
    phone = fields.Char(string="Téléphone", required=True)
    email = fields.Char(string="Adresse Email")
    
    # 🔐 LIEN PORTAL/WEB : Relie cette fiche à un compte utilisateur Odoo pour le futur Front-end
    user_id = fields.Many2one('res.users', string="Compte Utilisateur Web (Portail)")
    
    member_type = fields.Selection([
        ('beneficiary', 'Bénéficiaire (Maman/Enfant) 🧒'),
        ('volunteer', 'Bénévole de l\'association 🤝')
    ], string="Type de Membre", default='beneficiary', required=True)

    association_category = fields.Selection([
        ('maman', 'Maman solo / Famille 👩‍👦'),
        ('handicap', 'Neuroatypie / Handicap 🧠'),
        ('autre', 'Autre besoin spécifique 🌟')
    ], string="Catégorie Association", default='maman')
    
    # 🧠 CHAMPS SPECIFIQUES TSA / TDAH (Traduits en besoins concrets pour l'association)
    has_sensory_sensitivity = fields.Boolean(string="Sensibilité sensorielle (Bruit, Lumière...) 🎧")
    interests_or_hyperfocus = fields.Char(string="Centres d'intérêt / Intérêts spécifiques", placeholder="Ex: Les trains, les dinosaures (Aide pour capter son attention)")
    
    association_notes = fields.Text(string="Notes d'accompagnement spécifiques")
 
    # ---- Nouveaux champs pour les Bénévoles ----
    volunteer_specialty = fields.Selection([
        ('psy', 'Psychologue / Thérapeute 🧠'),
        ('edu', 'Éducateur spécialisé 🏫'),
        ('admin', 'Aide Administrative 📂'),
        ('listening', 'Écoute & Soutien ☕')
    ], string="Spécialité du Bénévole")
    
    is_available_weekend = fields.Boolean(string="Disponible le week-end 🗓️", default=False)

    # 🤝 L'aspect Humain : La Marraine dédiée à cette famille
    sponsor_id = fields.Many2one(
        'association.beneficiary', 
        string="Bénévole / Marraine dédiée 🤍",
        # 🛡️ Filtre strict : On ne peut choisir qu'un membre dont le type est 'volunteer'
        domain="[('member_type', '=', 'volunteer')]"
    )

    # 🔗 Le champ inverse : Permet au bénévole de voir toutes les mamans qu'il accompagne
    sponsored_member_ids = fields.One2many(
        'association.beneficiary', 
        'sponsor_id', 
        string="Familles parrainées"
    )

    # 🧸 Choix de l'avatar par défaut s'il n'y a pas de vraie photo
    default_avatar_type = fields.Selection([
        ('boy', 'Avatar Garçon 👦'),
        ('girl', 'Avatar Fille 👧'),
        ('neutral', 'Avatar Association 🏥')
    ], string="Avatar par défaut", default='neutral', required=True)


    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth:
                today = date.today()
                birth = record.date_of_birth
                record.age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            else:
                record.age = 0

    # =========================================================================
    # 🧸 FUSION DES NOUVEAUX CHAMPS DE SUIVI DE LUDOTHÈQUE (Côté Bénéficiaire)
    # =========================================================================
    
    # Correction : Le champ inverse dans l'historique est 'borrower_id' pour une maman !
    loan_history_ids = fields.One2many(
        'association.resource.loan.history', 
        'borrower_id', 
        string="Historique des emprunts de la famille"
    )

    late_loans_count = fields.Integer(
        string="Nombre de matériels en retard", 
        compute="_compute_late_loans_count"
    )

    # Historique de Ludothèque : intégration propre et optimisée v19
    @api.depends('loan_history_ids.return_date', 'loan_history_ids.due_date')
    def _compute_late_loans_count(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.loan_history_ids:
                # On filtre les lignes de CETTE maman qui n'ont pas de date de retour et dont l'échéance est passée
                late_loans = record.loan_history_ids.filtered(
                    lambda l: not l.return_date and l.due_date and l.due_date <= today
                )
                record.late_loans_count = len(late_loans)
            else:
                record.late_loans_count = 0


   # 🤝 FONCTION DE CRÉATION DE L'AVATAR AUTOMATIQUE (Version Odoo 19)
    
    # 🔄 CHANGEMENT DYNAMIQUE EN TEMPS RÉEL (Odoo 19)
    @api.onchange('default_avatar_type')
    def _onchange_default_avatar_type(self):
        """ Force le changement d'avatar en temps réel en utilisant pathlib (Garanti sans bug d'import) """
        from pathlib import Path
        
        # 📂 On détecte dynamiquement le dossier racine de VOTRE module :
        # __file__ correspond à : .../odoo_association_rdv/models/association_beneficiary.py
        # .parent.parent nous fait remonter directement à la racine : .../odoo_association_rdv/
        module_root = Path(__file__).resolve().parent.parent
        
        # 🧸 Détermination du nom du fichier image
        if self.default_avatar_type == 'boy':
            filename = 'avatar_boy.png'
        elif self.default_avatar_type == 'girl':
            filename = 'avatar_girl.png'
        else:
            filename = 'avatar_default.png'
            
        # 🎯 Construction du chemin absolu sécurisé
        img_path = module_root / 'static' / 'src' / 'img' / filename
        
        # 🔄 Lecture et encodage si le fichier existe
        if img_path.exists():
            try:
                with open(img_path, 'rb') as f:
                    self.image_128 = base64.b64encode(f.read()).decode('utf-8')
            except Exception:
                self.image_128 = False
        else:
            self.image_128 = False


    # 🤝 2. CREATE MULTI : Sécurité lors de la sauvegarde finale (ou imports bruts)
    @api.model_create_multi
    def create(self, vals_list):
        module_root = Path(__file__).resolve().parent.parent
        
        for vals in vals_list:
            # Si l'utilisateur n'a chargé aucune image manuellement
            if not vals.get('image_128'):
                avatar_type = vals.get('default_avatar_type', 'neutral')
                filename = 'avatar_default.png'
                
                if avatar_type == 'boy':
                    filename = 'avatar_boy.png'
                elif avatar_type == 'girl':
                    filename = 'avatar_girl.png'
                    
                img_path = module_root / 'static' / 'src' / 'img' / filename
                
                if img_path.exists():
                    try:
                        with open(img_path, 'rb') as f:
                            vals['image_128'] = base64.b64encode(f.read()).decode('utf-8')
                    except Exception:
                        pass
                        
        return super(AssociationBeneficiary, self).create(vals_list)

    # À ajouter dans la classe AssociationBeneficiary pour controle de nouveau maman inscrit
    registration_state = fields.Selection([
        ('pending', 'En attente de validation ⏳'),
        ('approved', 'Adhésion validée ✅')
    ], string="Statut d'inscription", default='pending', tracking=True)

    def action_approve_and_create_portal_user(self):
        """ Valide la maman, crée son compte Portail Odoo et lui envoie l'email de mot de passe """
        portal_group = self.env.ref('base.group_portal')
        for record in self:
            if not record.email:
                raise models.ValidationError("Veuillez renseigner une adresse email avant de créer l'accès web.")
            
            # Si aucun compte utilisateur n'est encore lié
            if not record.user_id:
                # Vérifie si un utilisateur avec cet email existe déjà
                existing_user = self.env['res.users'].sudo().search([('login', '=', record.email)], limit=1)
                if existing_user:
                    record.user_id = existing_user.id
                else:
                    # Crée l'utilisateur en mode PORTAIL uniquement
                    new_user = self.env['res.users'].sudo().with_context(no_reset_password=False).create({
                        'name': record.name,
                        'login': record.email,
                        'email': record.email,
                        'groups_id': [(6, 0, [portal_group.id])],
                    })
                    record.user_id = new_user.id
            
            record.registration_state = 'approved'




 
   
    
