from odoo import api, fields, models
from odoo.exceptions import ValidationError


class OdkPricingGrid(models.Model):
    """A pricing grid groups all tiers (paliers XS / S / M / L / XL / XXL)
    for a given commercial offer within a catalog.

    Typical layout V1
    -----------------
    * Catalog "Packs Factures" :
        - Grid "OFFRE_1"  (spot 0,22 EUR HT/facture)
        - Grid "OFFRE_2"  (bundle + PA, spot 0,28 EUR HT/facture)

    * Catalog "Abonnement ODK" :
        - Grid "PA_ODK"    (PA fournie par ODK)
        - Grid "PA_TIERCE" (PA tierce, surcharge par transaction)

    Grids are shared multi-company by default (``company_id = False``) and
    versionable via ``valid_from`` / ``valid_to``.
    """

    _name = 'odk.pricing.grid'
    _description = "ODK Pricing Grid"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'catalog_id, sequence, name'

    name = fields.Char(string="Nom", required=True, translate=True, tracking=True)
    code = fields.Char(
        string="Code",
        required=True,
        tracking=True,
        help="Code technique stable utilise par le wizard. "
             "Ex: OFFRE_1, OFFRE_2, PA_ODK, PA_TIERCE.",
    )
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Actif", default=True, tracking=True)

    catalog_id = fields.Many2one(
        comodel_name='odk.pricing.catalog',
        string="Catalogue",
        required=True,
        ondelete='cascade',
    )
    catalog_type = fields.Selection(
        related='catalog_id.catalog_type',
        store=True,
        readonly=True,
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Societe",
        help="Laisser vide pour partager la grille entre toutes les societes.",
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Devise",
        required=True,
        default=lambda self: self.env.ref('base.EUR'),
    )

    valid_from = fields.Date(string="Valide du", tracking=True)
    valid_to = fields.Date(string="Valide jusqu'au", tracking=True)

    # ------------------------------------------------------------------
    # Champs specifiques "Packs Factures" (catalog_type = 'volume')
    # ------------------------------------------------------------------
    spot_price = fields.Monetary(
        string="Prix spot HT (depassement)",
        currency_field='currency_id',
        tracking=True,
        help="Prix unitaire HT applique aux factures au-dela du volume du "
             "palier. Ex: 0,22 EUR pour OFFRE_1, 0,28 EUR pour OFFRE_2.",
    )
    floor_price = fields.Monetary(
        string="Plancher tarifaire HT",
        currency_field='currency_id',
        tracking=True,
        help="Prix unitaire HT minimum negociable par facture. "
             "Defaut ODK : 0,18 EUR. Variable definie par l'Admin Tarifaire "
             "et appliquee comme controle bloquant a la confirmation du devis.",
    )

    # ------------------------------------------------------------------
    # Champs specifiques "Abonnement ODK" (catalog_type = 'network')
    # ------------------------------------------------------------------
    overage_caisse_price = fields.Monetary(
        string="Depassement caisse / mois",
        currency_field='currency_id',
        tracking=True,
        help="Surcharge mensuelle HT par caisse supplementaire au-dela du "
             "palier. Defaut : 4 EUR/mois.",
    )
    overage_tx_price = fields.Monetary(
        string="Depassement transaction (HT)",
        currency_field='currency_id',
        tracking=True,
        help="Surcharge HT par transaction au-dela du palier. "
             "Defaut : 0,008 EUR/tx.",
    )

    # ------------------------------------------------------------------
    # Relations
    # ------------------------------------------------------------------
    tier_ids = fields.One2many(
        comodel_name='odk.pricing.tier',
        inverse_name='grid_id',
        string="Paliers",
    )
    tier_count = fields.Integer(
        string="Nb paliers",
        compute='_compute_tier_count',
    )

    _sql_constraints = [
        ('odk_pricing_grid_code_catalog_uniq',
         'unique(code, catalog_id)',
         "Le code de la grille doit etre unique au sein d'un catalogue."),
    ]

    @api.depends('tier_ids')
    def _compute_tier_count(self):
        for grid in self:
            grid.tier_count = len(grid.tier_ids)

    @api.constrains('valid_from', 'valid_to')
    def _check_validity_window(self):
        for grid in self:
            if grid.valid_from and grid.valid_to and grid.valid_from > grid.valid_to:
                raise ValidationError(
                    "La date de fin de validite doit etre posterieure a la date de debut."
                )

    @api.constrains('floor_price', 'spot_price')
    def _check_floor_below_spot(self):
        for grid in self:
            if grid.catalog_type != 'volume':
                continue
            if grid.floor_price and grid.spot_price and grid.floor_price > grid.spot_price:
                raise ValidationError(
                    "Le plancher tarifaire (%s) ne peut pas exceder le prix spot (%s)."
                    % (grid.floor_price, grid.spot_price)
                )

    def find_tier_for_metric(self, metric_value):
        """Return the tier whose threshold range contains ``metric_value``.

        * For 'volume' catalogs the metric is the annual invoice volume :
          we pick the smallest tier whose ``volume_annuel`` is >= metric_value
          (the customer's volume fits in that pack). If volume exceeds the
          largest tier, we return the largest one (overage handled via spot).

        * For 'network' catalogs the metric is the number of shops :
          we pick the tier whose ``shop_min`` <= metric_value <= ``shop_max``
          (with ``shop_max = 0`` meaning unlimited).
        """
        self.ensure_one()
        tiers = self.tier_ids.filtered('active').sorted('sequence')
        if not tiers:
            raise ValidationError("La grille '%s' ne contient aucun palier actif." % self.name)

        if self.catalog_type == 'volume':
            fit = tiers.filtered(lambda t: t.volume_annuel and t.volume_annuel >= metric_value)
            return fit[:1] or tiers[-1]

        if self.catalog_type == 'network':
            for tier in tiers:
                if tier.shop_min <= metric_value and (tier.shop_max == 0 or metric_value <= tier.shop_max):
                    return tier
            raise ValidationError(
                "Aucun palier de la grille '%s' ne contient la valeur %s magasins."
                % (self.name, metric_value)
            )

        raise ValidationError("Type de catalogue inconnu : %s" % self.catalog_type)
