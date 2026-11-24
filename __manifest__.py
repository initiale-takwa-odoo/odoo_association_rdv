# -*- coding: utf-8 -*-
{
    'name': 'Association Solidaire : Prise de RDV 🏥',
    'version': '1.0',
    'summary': "Organisation des rendez-vous et suivi des bénéficiaires de l'association",
    'category': 'Humanitarian',
    'author': 'Ajili Takwa (Freelance)',
    'depends': [
        'base', 
        'web', 
        'mail', 
        'calendar'
    ],
    'data': [
        'security/association_security.xml', # 1. LES RÈGLES ET GROUPES XML EN PREMIER 🛡️
        'security/ir.model.access.csv',      # 2. LES ACCÈS CSV EN DEUXIÈME 📋
        'views/association_views.xml',         # 3. LES ÉCRANS ET VUES EN DERNIER 🎨
        'views/association_website_templates.xml', 
    ],

    'assets': {
    'web.assets_frontend': [
        'odoo_association_rdv/static/src/css/association.css',
    ],
    },
    
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
