from odoo import _, api, fields, models


class ResPartner(models.Model):
    """Extension de res.partner pour exposer un bouton intelligent vers les
    devis ODK rattaches au contact."""

    _inherit = 'res.partner'

    odk_quote_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='partner_id',
        string="Devis ODK",
        domain=[('odk_is_quote', '=', True)],
    )
    odk_quote_count = fields.Integer(
        string="Nombre de devis ODK",
        compute='_compute_odk_quote_count',
    )

    def _compute_odk_quote_count(self):
        """Utilise search_count pour eviter de charger en RAM tout le recordset
        de devis lies au contact (couteux sur les grands volumes)."""
        SaleOrder = self.env['sale.order']
        for partner in self:
            partner.odk_quote_count = SaleOrder.search_count([
                ('partner_id', '=', partner.id),
                ('odk_is_quote', '=', True),
            ])

    def action_view_odk_quotes(self):
        """Bouton intelligent : ouvre la liste des devis ODK du contact."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Devis ODK"),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', '=', self.id),
                ('odk_is_quote', '=', True),
            ],
            'context': {
                'default_partner_id': self.id,
                'search_default_partner_id': self.id,
            },
        }
