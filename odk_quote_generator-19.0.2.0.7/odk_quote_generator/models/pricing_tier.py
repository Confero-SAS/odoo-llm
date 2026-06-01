from odoo import api, fields, models
from odoo.exceptions import ValidationError


class OdkPricingTier(models.Model):
    """A pricing tier (palier) represents one row of a pricing grid.

    Same model handles both catalog types ; only the relevant fields are
    populated based on the parent grid's ``catalog_type`` :

    * 'volume' (Packs Factures) uses :
        - ``volume_annuel`` (cap du palier)
        - ``unit_price_12m`` / ``_24m`` / ``_36m`` (prix unitaire HT par facture)

    * 'network' (Abonnement ODK) uses :
        - ``shop_min`` / ``shop_max`` (bornes du palier reseau)
        - ``caisses_included`` (nb de caisses incluses par magasin)
        - ``tx_caisse_mois`` (transactions/caisse/mois incluses)
        - ``unit_price_12m`` / ``_24m`` / ``_36m`` (loyer HT mensuel par magasin)
        - ``surcharge_pa_tiers_tx`` (surcharge HT/tx si PA fournie par un tiers)
    """

    _name = 'odk.pricing.tier'
    _description = "ODK Pricing Tier (palier)"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'grid_id, sequence, code'

    code = fields.Char(
        string="Code palier",
        required=True,
        tracking=True,
        help="Code court du palier. Ex: XS, S, M, L, XL, XXL.",
    )
    libelle = fields.Char(
        string="Libelle",
        translate=True,
        tracking=True,
        help="Libelle commercial. Ex: 'Tres petit reseau', 'Grand reseau'.",
    )
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Actif", default=True, tracking=True)

    grid_id = fields.Many2one(
        comodel_name='odk.pricing.grid',
        string="Grille",
        required=True,
        ondelete='cascade',
    )
    catalog_type = fields.Selection(
        related='grid_id.catalog_type',
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        related='grid_id.currency_id',
        store=True,
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Champs Packs Factures (catalog_type = 'volume')
    # ------------------------------------------------------------------
    volume_annuel = fields.Integer(
        string="Volume annuel (factures)",
        tracking=True,
        help="Plafond annuel du palier en nombre de factures. "
             "Ex: S=100 000, M=250 000, L=500 000, XL=1 000 000, XXL=2 000 000.",
    )

    # ------------------------------------------------------------------
    # Champs Abonnement ODK (catalog_type = 'network')
    # ------------------------------------------------------------------
    shop_min = fields.Integer(
        string="Magasins min.",
        tracking=True,
        help="Borne inferieure du palier reseau (inclusive).",
    )
    shop_max = fields.Integer(
        string="Magasins max.",
        tracking=True,
        help="Borne superieure du palier reseau (inclusive). "
             "Mettre 0 pour 'illimite' (palier XXL).",
    )
    caisses_included = fields.Integer(
        string="Caisses incluses / magasin",
        tracking=True,
        help="Nombre de caisses incluses par magasin dans le forfait du palier.",
    )
    tx_caisse_mois = fields.Integer(
        string="Transactions / caisse / mois incluses",
        tracking=True,
    )
    surcharge_pa_tiers_tx = fields.Monetary(
        string="Surcharge PA tierce / tx",
        currency_field='currency_id',
        tracking=True,
        help="Surcharge HT par transaction si la PA est fournie par un tiers "
             "(au lieu d'ODK).",
    )

    # ------------------------------------------------------------------
    # Prix HT par duree d'engagement (commun aux deux types)
    # ------------------------------------------------------------------
    unit_price_12m = fields.Monetary(
        string="Prix HT 12 mois",
        currency_field='currency_id',
        tracking=True,
        help="Packs : prix unitaire HT par facture. "
             "Abonnement : loyer HT mensuel par magasin.",
    )
    unit_price_24m = fields.Monetary(
        string="Prix HT 24 mois",
        currency_field='currency_id',
        tracking=True,
    )
    unit_price_36m = fields.Monetary(
        string="Prix HT 36 mois",
        currency_field='currency_id',
        tracking=True,
    )

    display_name = fields.Char(compute='_compute_display_name', store=False)

    _sql_constraints = [
        ('odk_pricing_tier_code_grid_uniq',
         'unique(code, grid_id)',
         "Le code de palier doit etre unique au sein d'une grille."),
    ]

    @api.depends('code', 'libelle', 'grid_id.name')
    def _compute_display_name(self):
        for tier in self:
            label = tier.libelle and ' - ' + tier.libelle or ''
            tier.display_name = "[%s] %s%s" % (tier.code or '?', tier.grid_id.name or '', label)

    @api.constrains('unit_price_12m', 'unit_price_24m', 'unit_price_36m')
    def _check_price_decreasing(self):
        """Les engagements plus longs ne peuvent pas etre plus chers."""
        for tier in self:
            p12, p24, p36 = tier.unit_price_12m, tier.unit_price_24m, tier.unit_price_36m
            if p12 and p24 and p24 > p12:
                raise ValidationError(
                    "Palier %s : le prix 24 mois (%s) ne peut pas exceder le 12 mois (%s)."
                    % (tier.code, p24, p12)
                )
            if p24 and p36 and p36 > p24:
                raise ValidationError(
                    "Palier %s : le prix 36 mois (%s) ne peut pas exceder le 24 mois (%s)."
                    % (tier.code, p36, p24)
                )

    @api.constrains('shop_min', 'shop_max', 'catalog_type')
    def _check_shop_range(self):
        for tier in self:
            if tier.catalog_type != 'network':
                continue
            if tier.shop_min < 0 or tier.shop_max < 0:
                raise ValidationError("Palier %s : bornes magasin negatives non autorisees." % tier.code)
            if tier.shop_max and tier.shop_min > tier.shop_max:
                raise ValidationError(
                    "Palier %s : borne min (%s) > borne max (%s)."
                    % (tier.code, tier.shop_min, tier.shop_max)
                )

    @api.constrains('volume_annuel', 'catalog_type')
    def _check_volume_positive(self):
        for tier in self:
            if tier.catalog_type == 'volume' and (not tier.volume_annuel or tier.volume_annuel <= 0):
                raise ValidationError(
                    "Palier %s : le volume annuel doit etre strictement positif." % tier.code
                )

    # ------------------------------------------------------------------
    # Helpers de calcul - utilises par le wizard (tache #22)
    # ------------------------------------------------------------------
    def get_unit_price(self, engagement_months):
        """Renvoie le prix HT du palier pour l'engagement demande (12/24/36)."""
        self.ensure_one()
        if engagement_months == 12:
            return self.unit_price_12m
        if engagement_months == 24:
            return self.unit_price_24m
        if engagement_months == 36:
            return self.unit_price_36m
        raise ValidationError(
            "Duree d'engagement non supportee : %s mois (attendu : 12, 24 ou 36)."
            % engagement_months
        )

    def compute_packs_monthly(self, engagement_months):
        """Pack mensualite = volume_annuel x prix_unitaire / 12."""
        self.ensure_one()
        if self.catalog_type != 'volume':
            raise ValidationError(
                "compute_packs_monthly() reserve aux paliers de catalogue volumetrique."
            )
        return (self.volume_annuel or 0) * self.get_unit_price(engagement_months) / 12.0

    def compute_subscription_monthly(self, nb_shops, engagement_months, pa_tierce=False, nb_caisses=None, tx_total=None):
        """Loyer mensuel HT abonnement pour un client donne.

        :param nb_shops: nombre de magasins
        :param engagement_months: 12, 24 ou 36
        :param pa_tierce: True si PA fournie par un tiers (applique surcharge)
        :param nb_caisses: total caisses (sinon = nb_shops * caisses_included)
        :param tx_total: total transactions/mois (sinon = caisses * tx_caisse_mois)
        :return: dict {base, overage_caisses, overage_tx, surcharge_pa, total}
        """
        self.ensure_one()
        if self.catalog_type != 'network':
            raise ValidationError(
                "compute_subscription_monthly() reserve aux paliers de catalogue reseau."
            )

        base_unit = self.get_unit_price(engagement_months)
        base = nb_shops * base_unit

        included_caisses = nb_shops * (self.caisses_included or 0)
        actual_caisses = nb_caisses if nb_caisses is not None else included_caisses
        extra_caisses = max(actual_caisses - included_caisses, 0)
        overage_caisses = extra_caisses * (self.grid_id.overage_caisse_price or 0)

        included_tx = actual_caisses * (self.tx_caisse_mois or 0)
        actual_tx = tx_total if tx_total is not None else included_tx
        extra_tx = max(actual_tx - included_tx, 0)
        overage_tx = extra_tx * (self.grid_id.overage_tx_price or 0)

        surcharge_pa = (actual_tx * (self.surcharge_pa_tiers_tx or 0)) if pa_tierce else 0.0

        return {
            'base':            base,
            'overage_caisses': overage_caisses,
            'overage_tx':      overage_tx,
            'surcharge_pa':    surcharge_pa,
            'total':           base + overage_caisses + overage_tx + surcharge_pa,
        }
