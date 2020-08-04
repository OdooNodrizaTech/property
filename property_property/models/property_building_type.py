# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PropertyBuildingType(models.Model):
    _name = 'property.building.type'
    _description = 'Property Building Type'

    external_id = fields.Char(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
    )
