# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

class PropertyPropertyBuildUnit(models.Model):
    _name = 'property.property.build.unit'
    _description = 'Property Property Build Unit'
    
    property_property_id = fields.Many2one(
        comodel_name='property.property',
        string='Property Property Id'
    )
    external_id = fields.Char(
        string='External Id'
    )
    stair = fields.Char(
        string='Stair'
    )
    floor = fields.Char(
        string='Floor'
    )
    door = fields.Char(
        string='Door'
    )
    built_surface_area = fields.Integer(
        string='Built Surface Area'
    )
    property_use_id = fields.Many2one(
        comodel_name='property.use',
        string='Property Use Id'
    )
    property_building_type_id = fields.Many2one(
        comodel_name='property.building.type',
        string='Property Building Type Id'
    )            
    source = fields.Selection(
        selection=[
            ('bbva','BBVA')                                      
        ],
        string='Source',
        default='bbva'
    )    