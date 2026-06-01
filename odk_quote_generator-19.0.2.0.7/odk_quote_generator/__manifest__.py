{
    'name': "ODK - Generateur de Devis Automatique",
    'summary': "Generation automatique de devis ODK mixtes (Packs Factures ET/OU "
               "Abonnement dans un meme devis) a partir de grilles tarifaires "
               "configurables, avec rapport PDF au look one-pager.",
    'description': """
ODK Quote Generator
===================

Module Odoo 19 developpe pour ODK (Groupe Confero) permettant la generation
automatique de devis a partir de variables saisies par l'utilisateur.

Catalogues V1
-------------
* **Packs Factures** (V4) : 5 paliers volumetriques (S/M/L/XL/XXL), 2 offres
  (Offre 1 spot 0,22 EUR / Offre 2 bundle + PA spot 0,28 EUR), engagements
  12/24/36 mois, plancher tarifaire 0,18 EUR HT/facture.

* **Abonnement ODK** (V1) : 6 paliers reseau (XS/S/M/L/XL/XXL), 2 offres
  (avec PA ODK / avec PA tierce surchargee), engagements 12/24/36 mois,
  8 fonctionnalites, depassements caisses (+4 EUR/mois) et transactions
  (+0,008 EUR/tx).

Nouveautes V2
-------------
* **Devis mixte** : un meme devis peut desormais combiner une offre Packs
  Factures ET une offre Abonnement ODK. Le wizard propose deux sections
  activables independamment (cases "Inclure Packs Factures" / "Inclure
  Abonnement ODK") avec leurs propres grilles, engagements et apercus.
* **Rapport PDF "one-pager"** : refonte de la charte (en-tete blanc a liseré
  orange, badge de mise en avant, titres de section soulignes, tables a
  en-tete NAVY et colonnes label grises, pied de page gris). Le PDF affiche
  les conditions tarifaires des deux sections pour un devis mixte.

Fonctionnalites
---------------
* Grilles tarifaires partagees multi-societes, reconfigurables sans modification
  de code.
* Wizard de saisie convivial : nombre de magasins/caisses/volume → devis genere.
* Devis injecte dans le pipeline commercial (sale.order) et rattache au contact
  (res.partner) + opportunite (crm.lead).
* Rapport PDF aux couleurs ODK (NAVY #1F3864 / ORANGE #ED7D31) avec logo et
  charte graphique.
* Detection automatique hors-grille ligne a ligne (deux grilles distinctes
  possibles dans un devis mixte) avec workflow de validation manager.
* Gestion fine des droits via 4 groupes metier.

Groupes de securite
-------------------
* **Commercial ODK** : creer/modifier ses devis dans la grille.
* **Manager Commercial ODK** : valider les devis hors-grille (override prix).
* **Admin Tarifaire ODK** : gerer les catalogues, grilles et paliers.
* **Direction ODK** : consultation transverse (lecture seule).
""",
    'author': "ODK / Groupe Confero",
    'website': "https://www.odk.fr",
    'maintainer': "ODK - Direction des Operations",
    'license': 'OPL-1',
    'category': 'Sales/Sales',
    'version': '19.0.2.0.7',

    'depends': [
        'base',
        'mail',
        'product',
        'sale_management',
        'crm',
    ],

    'data': [
        # Security must be loaded first (groups before ACLs that reference them)
        'security/odk_security.xml',
        'security/ir.model.access.csv',
        # Initial data - catalogs first, then grids/tiers that reference them
        'data/odk_catalogs.xml',
        'data/odk_packs_factures.xml',
        'data/odk_abonnement.xml',
        # Views - pricing models first, then sale.order/partner/lead extensions
        'views/odk_pricing_views.xml',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        # Menus - define parent menus first
        'views/odk_menus.xml',
        # Wizard view + sub-menu (references parent menu_odk_quotes from odk_menus.xml)
        'wizards/quote_generator_wizard_views.xml',
        # Reports - paperformat first, then action + templates
        'reports/odk_quote_report.xml',
        'reports/odk_quote_report_templates.xml',
    ],

    'demo': [],

    # Odoo 19 : les styles de rapport se declarent dans le bundle d'assets
    # 'web.report_assets_common' via le manifeste (on ne peut plus heriter
    # le template QWeb du meme nom).
    'assets': {
        'web.report_assets_common': [
            'odk_quote_generator/static/src/css/odk_report.css',
        ],
    },

    'application': True,
    'installable': True,
    'auto_install': False,
}
