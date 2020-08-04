# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DistritopostalWay(models.Model):
    _inherit = 'distritopostal.way'
    
    property_way_id = fields.Many2one(
        comodel_name='property.way',
        string='Property Way'
    )
