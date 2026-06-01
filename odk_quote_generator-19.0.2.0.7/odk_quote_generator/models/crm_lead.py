from odoo import _, api, fields, models


class CrmLead(models.Model):
    """Extension de crm.lead pour exposer un bouton intelligent vers les
    devis ODK rattaches a l'opportunite."""

    _inherit = 'crm.lead'

    odk_quote_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='opportunity_id',
        string="Devis ODK",
        domain=[('odk_is_quote', '=', True)],
    )
    odk_quote_count = fields.Integer(
        string="Nombre de devis ODK",
        compute='_compute_odk_quote_count',
    )

    def _compute_odk_quote_count(self):
        """Utilise search_count pour eviter de charger en RAM tout le recordset
        de devis lies a l'opportunite (couteux sur les grands volumes)."""
        SaleOrder = self.env['sale.order']
        for lead in self:
            lead.odk_quote_count = SaleOrder.search_count([
                ('opportunity_id', '=', lead.id),
                ('odk_is_quote', '=', True),
            ])

    def action_view_odk_quotes(self):
        """Bouton intelligent : ouvre la liste des devis ODK de l'opportunite."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Devis ODK"),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [
                ('opportunity_id', '=', self.id),
                ('odk_is_quote', '=', True),
            ],
            'context': {
                'default_opportunity_id': self.id,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'search_default_opportunity_id': self.id,
            },
        }
