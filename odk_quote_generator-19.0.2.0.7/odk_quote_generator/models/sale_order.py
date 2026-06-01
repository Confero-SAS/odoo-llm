from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class SaleOrder(models.Model):
    """Extension de sale.order pour les devis generes par le module ODK.

    Un devis est dit "ODK" des qu'il porte un ``odk_catalog_id``. Cela permet
    de filtrer les devis du module dans les vues, les rapports et les boutons
    smart des fiches contact / opportunite, sans devoir creer un nouveau
    modele.
    """

    _inherit = 'sale.order'

    # ------------------------------------------------------------------
    # Provenance tarifaire (rempli par le wizard - tache #22)
    # ------------------------------------------------------------------
    odk_catalog_id = fields.Many2one(
        comodel_name='odk.pricing.catalog',
        string="Catalogue ODK",
        index=True,
        copy=False,
        help="Catalogue ODK utilise comme source du devis. "
             "Non vide => le devis est considere comme un devis ODK.",
    )
    odk_grid_id = fields.Many2one(
        comodel_name='odk.pricing.grid',
        string="Grille tarifaire",
        domain="[('catalog_id', '=', odk_catalog_id), ('active', '=', True)]",
        index=True,
        copy=False,
    )
    odk_tier_id = fields.Many2one(
        comodel_name='odk.pricing.tier',
        string="Palier",
        domain="[('grid_id', '=', odk_grid_id), ('active', '=', True)]",
        index=True,
        copy=False,
    )
    odk_engagement_months = fields.Selection(
        selection=[
            ('12', "12 mois"),
            ('24', "24 mois"),
            ('36', "36 mois"),
        ],
        string="Engagement",
        index=True,
        copy=False,
    )

    # ------------------------------------------------------------------
    # Provenance tarifaire - section Abonnement (devis mixte)
    # ------------------------------------------------------------------
    odk_ab_catalog_id = fields.Many2one(
        comodel_name='odk.pricing.catalog',
        string="Catalogue Abonnement",
        index=True,
        copy=False,
        help="Catalogue Abonnement ODK present sur le devis (section reseau).",
    )
    odk_ab_grid_id = fields.Many2one(
        comodel_name='odk.pricing.grid',
        string="Grille Abonnement",
        domain="[('catalog_id', '=', odk_ab_catalog_id), ('active', '=', True)]",
        index=True,
        copy=False,
    )
    odk_ab_tier_id = fields.Many2one(
        comodel_name='odk.pricing.tier',
        string="Palier Abonnement",
        domain="[('grid_id', '=', odk_ab_grid_id), ('active', '=', True)]",
        index=True,
        copy=False,
    )
    odk_ab_engagement_months = fields.Selection(
        selection=[
            ('12', "12 mois"),
            ('24', "24 mois"),
            ('36', "36 mois"),
        ],
        string="Engagement Abonnement",
        index=True,
        copy=False,
    )
    odk_is_mixed = fields.Boolean(
        string="Devis mixte",
        copy=False,
        index=True,
        help="Vrai si le devis combine une offre Packs Factures ET une offre "
             "Abonnement ODK.",
    )

    # ------------------------------------------------------------------
    # Variables d'entree du wizard, persistees pour tracabilite
    # ------------------------------------------------------------------
    odk_input_shops = fields.Integer(
        string="Nb magasins (saisi)",
        copy=False,
        help="Variable d'entree du wizard (abonnement uniquement).",
    )
    odk_input_volume_annuel = fields.Integer(
        string="Volume annuel saisi (factures)",
        copy=False,
        help="Variable d'entree du wizard (packs factures uniquement).",
    )
    odk_input_pa_tierce = fields.Boolean(
        string="PA tierce",
        copy=False,
        help="Coche => la PA n'est pas fournie par ODK, la surcharge par "
             "transaction est appliquee (abonnement uniquement).",
    )
    odk_input_nb_caisses = fields.Integer(
        string="Total caisses saisi",
        copy=False,
    )
    odk_input_tx_total = fields.Integer(
        string="Total transactions / mois saisi",
        copy=False,
    )

    # ------------------------------------------------------------------
    # Validation hors-grille
    # ------------------------------------------------------------------
    odk_is_off_grid = fields.Boolean(
        string="Hors grille",
        copy=False,
        index=True,
        help="Coche automatiquement quand un prix de ligne s'ecarte du tarif "
             "calcule a partir de la grille / palier / engagement choisis, "
             "OU quand un prix passe sous le plancher tarifaire de la grille.",
    )
    odk_is_validated = fields.Boolean(
        string="Hors-grille valide",
        copy=False,
        index=True,
        help="Validation du Manager Commercial pour autoriser la confirmation "
             "d'un devis hors-grille.",
    )
    odk_validation_user_id = fields.Many2one(
        comodel_name='res.users',
        string="Valide par",
        copy=False,
        readonly=True,
    )
    odk_validation_date = fields.Datetime(
        string="Date de validation",
        copy=False,
        readonly=True,
    )

    odk_is_quote = fields.Boolean(
        string="Devis ODK",
        compute='_compute_odk_is_quote',
        store=True,
        index=True,
        help="True si le devis a ete genere par le wizard ODK "
             "(catalogue Packs et/ou Abonnement renseigne).",
    )

    # ==================================================================
    # Calculs
    # ==================================================================
    @api.depends('odk_catalog_id', 'odk_ab_catalog_id')
    def _compute_odk_is_quote(self):
        for order in self:
            order.odk_is_quote = bool(order.odk_catalog_id or order.odk_ab_catalog_id)

    @api.onchange('odk_catalog_id')
    def _onchange_odk_catalog_id(self):
        for order in self:
            if order.odk_grid_id and order.odk_grid_id.catalog_id != order.odk_catalog_id:
                order.odk_grid_id = False
                order.odk_tier_id = False

    @api.onchange('odk_grid_id')
    def _onchange_odk_grid_id(self):
        for order in self:
            if order.odk_tier_id and order.odk_tier_id.grid_id != order.odk_grid_id:
                order.odk_tier_id = False

    @api.onchange('odk_ab_catalog_id')
    def _onchange_odk_ab_catalog_id(self):
        for order in self:
            if order.odk_ab_grid_id and order.odk_ab_grid_id.catalog_id != order.odk_ab_catalog_id:
                order.odk_ab_grid_id = False
                order.odk_ab_tier_id = False

    @api.onchange('odk_ab_grid_id')
    def _onchange_odk_ab_grid_id(self):
        for order in self:
            if order.odk_ab_tier_id and order.odk_ab_tier_id.grid_id != order.odk_ab_grid_id:
                order.odk_ab_tier_id = False

    # ==================================================================
    # Contraintes
    # ==================================================================
    @api.constrains('odk_catalog_id', 'odk_grid_id', 'odk_tier_id',
                    'odk_ab_catalog_id', 'odk_ab_grid_id', 'odk_ab_tier_id')
    def _check_odk_consistency(self):
        for order in self:
            if order.odk_grid_id and order.odk_catalog_id \
                    and order.odk_grid_id.catalog_id != order.odk_catalog_id:
                raise ValidationError(
                    _("La grille '%s' n'appartient pas au catalogue '%s'.")
                    % (order.odk_grid_id.name, order.odk_catalog_id.name)
                )
            if order.odk_tier_id and order.odk_grid_id \
                    and order.odk_tier_id.grid_id != order.odk_grid_id:
                raise ValidationError(
                    _("Le palier '%s' n'appartient pas a la grille '%s'.")
                    % (order.odk_tier_id.code, order.odk_grid_id.name)
                )
            if order.odk_ab_grid_id and order.odk_ab_catalog_id \
                    and order.odk_ab_grid_id.catalog_id != order.odk_ab_catalog_id:
                raise ValidationError(
                    _("La grille '%s' n'appartient pas au catalogue '%s'.")
                    % (order.odk_ab_grid_id.name, order.odk_ab_catalog_id.name)
                )
            if order.odk_ab_tier_id and order.odk_ab_grid_id \
                    and order.odk_ab_tier_id.grid_id != order.odk_ab_grid_id:
                raise ValidationError(
                    _("Le palier '%s' n'appartient pas a la grille '%s'.")
                    % (order.odk_ab_tier_id.code, order.odk_ab_grid_id.name)
                )

    # ==================================================================
    # Validation hors-grille (bouton accessible aux managers uniquement)
    # ==================================================================
    def action_odk_validate_off_grid(self):
        """Valide un devis ODK hors-grille. Reserve au Manager Commercial."""
        for order in self:
            if not order.odk_is_quote:
                raise UserError(_("Action reservee aux devis ODK."))
            if not order.odk_is_off_grid:
                raise UserError(_("Ce devis n'est pas hors-grille."))
            if not self.env.user.has_group('odk_quote_generator.group_odk_sales_manager'):
                raise UserError(
                    _("Seul un Manager Commercial peut valider un devis hors-grille.")
                )
            order._check_floor_price()
            order.write({
                'odk_is_validated': True,
                'odk_validation_user_id': self.env.user.id,
                'odk_validation_date': fields.Datetime.now(),
            })
            order.message_post(body=_(
                "Devis hors-grille valide par %s.", self.env.user.name
            ))
        return True

    def action_odk_revoke_validation(self):
        """Retire la validation hors-grille (ex: prix modifie apres validation)."""
        for order in self:
            if not order.odk_is_validated:
                continue
            order.write({
                'odk_is_validated': False,
                'odk_validation_user_id': False,
                'odk_validation_date': False,
            })
            order.message_post(body=_("Validation hors-grille retiree."))
        return True

    # ==================================================================
    # Plancher tarifaire (defini sur odk.pricing.grid.floor_price par
    # l'administrateur tarifaire) - blocage strict, non franchissable
    # meme par un Manager.
    # ==================================================================
    def _check_floor_price(self):
        """Verifie que chaque ligne ODK respecte le plancher de SA grille.

        Le plancher est une variable configuree par l'Admin Tarifaire sur
        ``odk.pricing.grid.floor_price``. Le controle est realise ligne a
        ligne : la grille de reference est ``line.odk_tier_id.grid_id``, ce
        qui permet a un devis mixte (Packs + Abonnement) de faire coexister
        deux grilles avec des planchers distincts. Un commercial OU un
        manager ne peut pas saisir un prix unitaire en-dessous du plancher,
        meme avec la validation hors-grille. Pour deroger, il faut faire
        evoluer la grille tarifaire (action Admin Tarifaire).
        """
        for order in self:
            if not order.odk_is_quote:
                continue
            for line in order.order_line:
                grid = line.odk_tier_id.grid_id if line.odk_tier_id else False
                if not grid:
                    continue
                floor = grid.floor_price
                if not floor:
                    continue
                currency = grid.currency_id
                precision = currency.decimal_places if currency else 4
                if float_compare(line.price_unit, floor, precision_digits=precision) < 0:
                    raise UserError(_(
                        "Ligne '%(line)s' : le prix unitaire saisi (%(price)s) "
                        "est inferieur au plancher tarifaire de la grille "
                        "'%(grid)s' (%(floor)s). Le plancher est une variable "
                        "definie par l'Admin Tarifaire et ne peut pas etre "
                        "franchi, meme par validation hors-grille.",
                        line=line.name or '?',
                        price=line.price_unit,
                        grid=grid.name,
                        floor=floor,
                    ))

    # ==================================================================
    # Verrou de confirmation : un devis hors-grille non valide ne peut pas
    # passer en commande sans l'aval d'un Manager Commercial, ET le
    # plancher tarifaire doit etre respecte sur toutes les lignes.
    # ==================================================================
    def action_confirm(self):
        for order in self:
            order._check_floor_price()
            if order.odk_is_quote and order.odk_is_off_grid and not order.odk_is_validated:
                raise UserError(_(
                    "Ce devis ODK est hors-grille et doit etre valide par un "
                    "Manager Commercial avant confirmation."
                ))
        return super().action_confirm()

    # ==================================================================
    # Recalcul du drapeau hors-grille apres modification des lignes.
    # Compare ligne a ligne le prix saisi vs. le prix attendu de la
    # grille, et detecte aussi un prix < plancher comme hors-grille.
    # ==================================================================
    def _odk_recompute_off_grid(self):
        for order in self:
            if not order.odk_is_quote:
                continue
            off = False
            for line in order.order_line:
                grid = line.odk_tier_id.grid_id if line.odk_tier_id else False
                currency = grid.currency_id if grid else order.currency_id
                precision = currency.decimal_places if currency else 4
                if line.odk_expected_unit_price and float_compare(
                        line.price_unit,
                        line.odk_expected_unit_price,
                        precision_digits=precision) != 0:
                    off = True
                    break
                floor = grid.floor_price if grid else 0.0
                if floor and line.odk_tier_id and float_compare(
                        line.price_unit, floor, precision_digits=precision) < 0:
                    off = True
                    break
            if order.odk_is_off_grid != off:
                order.odk_is_off_grid = off
                # Une modification de prix invalide automatiquement la validation
                if off and order.odk_is_validated:
                    order.action_odk_revoke_validation()


class SaleOrderLine(models.Model):
    """Marque chaque ligne de devis ODK avec le palier source, pour permettre
    au moteur de detection ``_odk_recompute_off_grid`` (cote sale.order) de
    comparer le prix saisi au prix attendu de la grille."""

    _inherit = 'sale.order.line'

    odk_tier_id = fields.Many2one(
        comodel_name='odk.pricing.tier',
        string="Palier ODK source",
        copy=False,
        help="Renseigne par le wizard. Sert au controle 'hors-grille'.",
    )
    odk_expected_unit_price = fields.Float(
        string="Prix unitaire attendu (grille)",
        copy=False,
        digits='Product Price',
        help="Prix unitaire HT calcule a partir de la grille au moment de la "
             "generation. Si le commercial modifie price_unit en s'ecartant "
             "de cette valeur, le devis bascule en 'hors-grille'.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.order_id._odk_recompute_off_grid()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ('price_unit', 'odk_expected_unit_price', 'odk_tier_id')):
            self.order_id._odk_recompute_off_grid()
        return res
