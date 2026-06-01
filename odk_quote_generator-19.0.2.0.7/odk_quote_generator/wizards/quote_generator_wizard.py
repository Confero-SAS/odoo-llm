from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OdkQuoteGeneratorWizard(models.TransientModel):
    """Wizard de generation automatique de devis ODK (devis mixte).

    Depuis la V2, un meme devis peut combiner DEUX offres :
      - une section Packs Factures (catalogue de type 'volume')
      - une section Abonnement ODK (catalogue de type 'network')

    L'utilisateur active l'une, l'autre, ou les deux via les cases
    ``include_packs`` / ``include_subscription``. Chaque section possede sa
    propre grille, son engagement, ses variables et son apercu. La generation
    cree UNE seule ``sale.order`` regroupant les lignes des deux sections.
    """

    _name = 'odk.quote.generator.wizard'
    _description = "Wizard de generation de devis ODK"

    # ------------------------------------------------------------------
    # Etape 1 : Contexte commercial
    # ------------------------------------------------------------------
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Client",
        required=True,
        domain="[('is_company', '=', True)]",
    )
    opportunity_id = fields.Many2one(
        comodel_name='crm.lead',
        string="Opportunite",
        domain="[('partner_id', '=', partner_id), ('type', '=', 'opportunity')]",
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Societe",
        required=True,
        default=lambda self: self.env.company,
    )

    # ------------------------------------------------------------------
    # Selection des sections du devis
    # ------------------------------------------------------------------
    include_packs = fields.Boolean(
        string="Inclure Packs Factures",
        default=True,
        help="Ajoute une offre Packs Factures (tarification au volume) au devis.",
    )
    include_subscription = fields.Boolean(
        string="Inclure Abonnement ODK",
        default=False,
        help="Ajoute une offre Abonnement ODK (tarification reseau) au devis.",
    )

    # ==================================================================
    # Section PACKS FACTURES (catalog_type = 'volume')
    # ==================================================================
    pk_grid_id = fields.Many2one(
        comodel_name='odk.pricing.grid',
        string="Offre Packs Factures",
        domain="[('catalog_type', '=', 'volume'), ('active', '=', True)]",
    )
    pk_engagement_months = fields.Selection(
        selection=[('12', "12 mois"), ('24', "24 mois"), ('36', "36 mois")],
        string="Engagement Packs",
        default='12',
    )
    volume_annuel = fields.Integer(
        string="Volume annuel (factures / an)",
        help="Volume previsionnel annuel utilise pour selectionner le palier.",
    )
    pk_tier_id = fields.Many2one(
        comodel_name='odk.pricing.tier',
        string="Palier Packs",
        readonly=True,
    )
    pk_expected_unit_price = fields.Float(
        string="Prix unitaire HT (palier Packs)",
        readonly=True,
        digits='Product Price',
    )
    pk_monthly_base = fields.Float(
        string="Base mensuelle HT (Packs)",
        readonly=True,
        digits='Product Price',
    )

    # ==================================================================
    # Section ABONNEMENT ODK (catalog_type = 'network')
    # ==================================================================
    ab_grid_id = fields.Many2one(
        comodel_name='odk.pricing.grid',
        string="Offre Abonnement",
        domain="[('catalog_type', '=', 'network'), ('active', '=', True)]",
    )
    ab_engagement_months = fields.Selection(
        selection=[('12', "12 mois"), ('24', "24 mois"), ('36', "36 mois")],
        string="Engagement Abonnement",
        default='12',
    )
    nb_shops = fields.Integer(
        string="Nombre de magasins",
        help="Sert au choix du palier (XS / S / M / L / XL / XXL).",
    )
    pa_tierce = fields.Boolean(
        string="PA fournie par un tiers",
        help="Coche => la PA n'est pas fournie par ODK. Sera appliquee une "
             "surcharge HT par transaction depuis le palier.",
    )
    nb_caisses = fields.Integer(
        string="Total caisses (estime)",
        help="Total caisses du parc. Si laisse a 0, calcul sur la base de "
             "magasins x caisses incluses.",
    )
    tx_total = fields.Integer(
        string="Total transactions / mois (estime)",
        help="Total transactions mensuelles. Si laisse a 0, calcul sur la base "
             "des transactions incluses du palier.",
    )
    ab_tier_id = fields.Many2one(
        comodel_name='odk.pricing.tier',
        string="Palier Abonnement",
        readonly=True,
    )
    ab_expected_unit_price = fields.Float(
        string="Loyer mensuel HT / magasin (palier)",
        readonly=True,
        digits='Product Price',
    )
    ab_monthly_base = fields.Float(
        string="Base mensuelle HT (Abonnement)",
        readonly=True,
        digits='Product Price',
    )
    ab_monthly_overage_caisses = fields.Float(
        string="Depassement caisses / mois",
        readonly=True,
        digits='Product Price',
    )
    ab_monthly_overage_tx = fields.Float(
        string="Depassement transactions / mois",
        readonly=True,
        digits='Product Price',
    )
    ab_monthly_surcharge_pa = fields.Float(
        string="Surcharge PA tierce / mois",
        readonly=True,
        digits='Product Price',
    )
    ab_monthly_total = fields.Float(
        string="Total mensuel HT (Abonnement)",
        readonly=True,
        digits='Product Price',
    )

    # ------------------------------------------------------------------
    # Recapitulatif combine
    # ------------------------------------------------------------------
    monthly_total_combined = fields.Float(
        string="Total mensuel HT (devis)",
        readonly=True,
        digits='Product Price',
    )

    # ==================================================================
    # Onchange - cascade et recalcul
    # ==================================================================
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.opportunity_id and self.opportunity_id.partner_id != self.partner_id:
            self.opportunity_id = False

    @api.onchange(
        'include_packs', 'include_subscription',
        'pk_grid_id', 'pk_engagement_months', 'volume_annuel',
        'ab_grid_id', 'ab_engagement_months',
        'nb_shops', 'pa_tierce', 'nb_caisses', 'tx_total',
    )
    def _onchange_recompute(self):
        for wiz in self:
            wiz._recompute_preview()

    # ==================================================================
    # Moteur de calcul (utilise par onchange ET par action_generate)
    # ==================================================================
    def _recompute_preview(self):
        """Met a jour les champs *preview* des deux sections."""
        self.ensure_one()

        # --- reset ---
        self.pk_tier_id = False
        self.pk_expected_unit_price = 0.0
        self.pk_monthly_base = 0.0
        self.ab_tier_id = False
        self.ab_expected_unit_price = 0.0
        self.ab_monthly_base = 0.0
        self.ab_monthly_overage_caisses = 0.0
        self.ab_monthly_overage_tx = 0.0
        self.ab_monthly_surcharge_pa = 0.0
        self.ab_monthly_total = 0.0
        self.monthly_total_combined = 0.0

        combined = 0.0

        # --- section Packs Factures ---
        if self.include_packs and self.pk_grid_id and self.pk_engagement_months \
                and self.volume_annuel and self.volume_annuel > 0:
            eng = int(self.pk_engagement_months)
            tier = self.pk_grid_id.find_tier_for_metric(self.volume_annuel)
            if tier:
                self.pk_tier_id = tier
                self.pk_expected_unit_price = tier.get_unit_price(eng)
                self.pk_monthly_base = tier.compute_packs_monthly(eng)
                combined += self.pk_monthly_base

        # --- section Abonnement ODK ---
        if self.include_subscription and self.ab_grid_id and self.ab_engagement_months \
                and self.nb_shops and self.nb_shops > 0:
            eng = int(self.ab_engagement_months)
            tier = self.ab_grid_id.find_tier_for_metric(self.nb_shops)
            if tier:
                self.ab_tier_id = tier
                self.ab_expected_unit_price = tier.get_unit_price(eng)
                res = tier.compute_subscription_monthly(
                    nb_shops=self.nb_shops,
                    engagement_months=eng,
                    pa_tierce=self.pa_tierce,
                    nb_caisses=self.nb_caisses or None,
                    tx_total=self.tx_total or None,
                )
                self.ab_monthly_base = res['base']
                self.ab_monthly_overage_caisses = res['overage_caisses']
                self.ab_monthly_overage_tx = res['overage_tx']
                self.ab_monthly_surcharge_pa = res['surcharge_pa']
                self.ab_monthly_total = res['total']
                combined += self.ab_monthly_total

        self.monthly_total_combined = combined

    # ==================================================================
    # Validation
    # ==================================================================
    def _validate_inputs(self):
        self.ensure_one()
        if not (self.include_packs or self.include_subscription):
            raise UserError(_(
                "Activez au moins une offre : Packs Factures et/ou Abonnement ODK."
            ))
        if self.include_packs:
            if not self.pk_grid_id:
                raise UserError(_("Section Packs : veuillez selectionner une offre."))
            if not self.volume_annuel or self.volume_annuel <= 0:
                raise UserError(_(
                    "Section Packs : veuillez saisir un volume annuel "
                    "previsionnel strictement positif."
                ))
        if self.include_subscription:
            if not self.ab_grid_id:
                raise UserError(_("Section Abonnement : veuillez selectionner une offre."))
            if not self.nb_shops or self.nb_shops <= 0:
                raise UserError(_(
                    "Section Abonnement : veuillez saisir un nombre de "
                    "magasins strictement positif."
                ))

    # ==================================================================
    # Action principale : generer la sale.order ODK
    # ==================================================================
    def action_generate_quote(self):
        """Cree la sale.order ODK (mixte) et ouvre la fiche en formulaire."""
        self.ensure_one()
        self._validate_inputs()
        self._recompute_preview()

        order_lines = []
        msg_parts = []

        # --- Section Packs ---
        pk_active = self.include_packs and self.pk_tier_id
        if self.include_packs and not self.pk_tier_id:
            raise UserError(_(
                "Section Packs : impossible de determiner le palier pour le "
                "volume saisi. Verifiez l'offre et le volume annuel."
            ))
        if pk_active:
            order_lines += self._build_packs_lines(int(self.pk_engagement_months))
            msg_parts.append(_(
                "Packs Factures : %(grid)s / palier %(tier)s / %(eng)s mois",
                grid=self.pk_grid_id.name,
                tier=self.pk_tier_id.code,
                eng=int(self.pk_engagement_months),
            ))

        # --- Section Abonnement ---
        ab_active = self.include_subscription and self.ab_tier_id
        if self.include_subscription and not self.ab_tier_id:
            raise UserError(_(
                "Section Abonnement : impossible de determiner le palier pour "
                "le nombre de magasins saisi. Verifiez l'offre et la saisie."
            ))
        if ab_active:
            order_lines += self._build_subscription_lines(int(self.ab_engagement_months))
            msg_parts.append(_(
                "Abonnement ODK : %(grid)s / palier %(tier)s / %(eng)s mois",
                grid=self.ab_grid_id.name,
                tier=self.ab_tier_id.code,
                eng=int(self.ab_engagement_months),
            ))

        if not order_lines:
            raise UserError(_(
                "Aucune ligne de devis n'a pu etre generee. Verifiez vos saisies."
            ))

        order_vals = {
            'partner_id':     self.partner_id.id,
            'opportunity_id': self.opportunity_id.id if self.opportunity_id else False,
            'company_id':     self.company_id.id,
            'odk_is_mixed':   bool(pk_active and ab_active),
            'order_line':     order_lines,
        }

        # Provenance Packs (champs historiques)
        if pk_active:
            order_vals.update({
                'odk_catalog_id':          self.pk_grid_id.catalog_id.id,
                'odk_grid_id':             self.pk_grid_id.id,
                'odk_tier_id':             self.pk_tier_id.id,
                'odk_engagement_months':   self.pk_engagement_months,
                'odk_input_volume_annuel': self.volume_annuel or 0,
            })

        # Provenance Abonnement (champs ab_*)
        if ab_active:
            order_vals.update({
                'odk_ab_catalog_id':        self.ab_grid_id.catalog_id.id,
                'odk_ab_grid_id':           self.ab_grid_id.id,
                'odk_ab_tier_id':           self.ab_tier_id.id,
                'odk_ab_engagement_months': self.ab_engagement_months,
                'odk_input_shops':          self.nb_shops or 0,
                'odk_input_pa_tierce':      self.pa_tierce,
                'odk_input_nb_caisses':     self.nb_caisses or 0,
                'odk_input_tx_total':       self.tx_total or 0,
            })

        order = self.env['sale.order'].create(order_vals)
        order.message_post(body=_(
            "Devis ODK genere automatiquement depuis le wizard. %s.",
            " + ".join(msg_parts),
        ))

        return {
            'type': 'ir.actions.act_window',
            'name': _("Devis ODK genere"),
            'res_model': 'sale.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ==================================================================
    # Construction des lignes - Packs Factures
    # ==================================================================
    def _build_packs_lines(self, eng):
        """Lignes Packs : 1 ligne forfait mensuel (volume mensuel moyen)."""
        self.ensure_one()
        unit_price = self.pk_expected_unit_price
        monthly_volume = self.volume_annuel / 12.0
        name = _(
            "%(grid)s - Palier %(tier)s - Engagement %(eng)s mois "
            "(facturation mensuelle, volume annuel %(vol)s factures, "
            "volume mensuel moyen %(mvol).2f factures)",
            grid=self.pk_grid_id.name,
            tier=self.pk_tier_id.code,
            eng=eng,
            vol=self.volume_annuel,
            mvol=monthly_volume,
        )
        return [(0, 0, {
            'name':                    name,
            'product_uom_qty':         monthly_volume,
            'price_unit':              unit_price,
            'odk_tier_id':             self.pk_tier_id.id,
            'odk_expected_unit_price': unit_price,
        })]

    # ==================================================================
    # Construction des lignes - Abonnement ODK
    # ==================================================================
    def _build_subscription_lines(self, eng):
        """Lignes Abonnement : forfait magasins + depassements + surcharge PA."""
        self.ensure_one()
        lines = []
        base_unit = self.ab_expected_unit_price
        name = _(
            "%s - Palier %s - Engagement %s mois - %s magasins (loyer mensuel HT/magasin)",
            self.ab_grid_id.name, self.ab_tier_id.code, eng, self.nb_shops,
        )
        lines.append((0, 0, {
            'name':                    name,
            'product_uom_qty':         self.nb_shops,
            'price_unit':              base_unit,
            'odk_tier_id':             self.ab_tier_id.id,
            'odk_expected_unit_price': base_unit,
        }))

        # Depassement caisses (si applicable)
        if self.ab_monthly_overage_caisses > 0:
            included = self.nb_shops * (self.ab_tier_id.caisses_included or 0)
            extra = max((self.nb_caisses or included) - included, 0)
            lines.append((0, 0, {
                'name': _(
                    "Depassement caisses : %s caisse(s) supplementaire(s) @ %s / mois",
                    extra, self.ab_grid_id.overage_caisse_price,
                ),
                'product_uom_qty': extra,
                'price_unit':      self.ab_grid_id.overage_caisse_price,
            }))

        # Depassement transactions (si applicable)
        if self.ab_monthly_overage_tx > 0:
            included_tx = (self.nb_caisses or self.nb_shops * (self.ab_tier_id.caisses_included or 0)) \
                          * (self.ab_tier_id.tx_caisse_mois or 0)
            extra_tx = max((self.tx_total or included_tx) - included_tx, 0)
            lines.append((0, 0, {
                'name': _(
                    "Depassement transactions : %s tx supplementaire(s) @ %s / tx",
                    extra_tx, self.ab_grid_id.overage_tx_price,
                ),
                'product_uom_qty': extra_tx,
                'price_unit':      self.ab_grid_id.overage_tx_price,
            }))

        # Surcharge PA tierce (si applicable)
        if self.pa_tierce and self.ab_monthly_surcharge_pa > 0:
            actual_tx = self.tx_total or (
                (self.nb_caisses or self.nb_shops * (self.ab_tier_id.caisses_included or 0))
                * (self.ab_tier_id.tx_caisse_mois or 0)
            )
            lines.append((0, 0, {
                'name': _(
                    "Surcharge PA tierce : %s tx @ %s / tx",
                    actual_tx, self.ab_tier_id.surcharge_pa_tiers_tx,
                ),
                'product_uom_qty': actual_tx,
                'price_unit':      self.ab_tier_id.surcharge_pa_tiers_tx,
            }))

        return lines
