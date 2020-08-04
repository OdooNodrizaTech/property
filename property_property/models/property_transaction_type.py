# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PropertyTransactionType(models.Model):
    _name = 'property.transaction.type'
    _description = 'Property Transaction Type'

    external_id = fields.Char(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
    )
