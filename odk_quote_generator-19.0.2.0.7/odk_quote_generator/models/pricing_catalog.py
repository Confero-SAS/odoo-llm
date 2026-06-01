from odoo import api, fields, models
from odoo.exceptions import ValidationError


class OdkPricingCatalog(models.Model):
    """Top-level catalog ODK regrouping one or several pricing grids.

    V1 ships two catalogs:
      * Packs Factures   (catalog_type = 'volume',  metric = annual invoice volume)
      * Abonnement ODK   (catalog_type = 'network', metric = number of shops)

    Catalogs are shared across companies (``company_id = False``) by default so
    that every filiale of Groupe Confero sees the same pricing.

    Heritage ``mail.thread`` + ``mail.activity.mixin`` : tracabilite des
    modifications tarifaires (qui a modifie quoi, quand) - exigence ANSSI
    domaine 12.
    """

    _name = 'odk.pricing.catalog'
    _description = "ODK Pricing Catalog"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(string="Nom", required=True, translate=True, tracking=True)
    code = fields.Char(
        string="Code",
        required=True,
        tracking=True,
        help="Code technique stable utilise par le wizard et les rapports. "
             "Ex: PACKS_FACTURES, ABONNEMENT_ODK.",
    )
    catalog_type = fields.Selection(
        selection=[
            ('volume',  "Volumetrique (Packs Factures)"),
            ('network', "Reseau (Abonnement ODK)"),
        ],
        string="Type de catalogue",
        required=True,
        tracking=True,
        help="Determine la metrique de selection du palier : "
             "volumetrique (nb factures/an) ou reseau (nb magasins).",
    )
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Actif", default=True, tracking=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Societe",
        help="Laisser vide pour partager le catalogue entre toutes les societes "
             "du groupe (cas par defaut chez ODK).",
    )

    grid_ids = fields.One2many(
        comodel_name='odk.pricing.grid',
        inverse_name='catalog_id',
        string="Grilles tarifaires",
    )
    grid_count = fields.Integer(
        string="Nb grilles",
        compute='_compute_grid_count',
    )

    _sql_constraints = [
        ('odk_pricing_catalog_code_uniq',
         'unique(code)',
         "Le code du catalogue doit etre unique."),
    ]

    @api.depends('grid_ids')
    def _compute_grid_count(self):
        for catalog in self:
            catalog.grid_count = len(catalog.grid_ids)

    @api.constrains('code')
    def _check_code_format(self):
        for catalog in self:
            if not catalog.code or not catalog.code.strip():
                raise ValidationError("Le code du catalogue est obligatoire.")
            if ' ' in catalog.code:
                raise ValidationError(
                    "Le code du catalogue ne doit pas contenir d'espace : %s" % catalog.code
                )

    def find_grid(self, grid_code):
        """Return the active grid of this catalog identified by ``grid_code``.

        Used by the wizard to resolve "Offre 1" / "Offre 2" without hardcoding
        database IDs.
        """
        self.ensure_one()
        grid = self.grid_ids.filtered(lambda g: g.active and g.code == grid_code)
        if not grid:
            raise ValidationError(
                "Aucune grille active avec le code '%s' dans le catalogue '%s'."
                % (grid_code, self.name)
            )
        return grid[:1]
