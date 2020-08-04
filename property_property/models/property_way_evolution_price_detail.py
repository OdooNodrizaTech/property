# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PropertyWayEvolutionPriceDetail(models.Model):
    _name = 'property.way.evolution.price.detail'
    _description = 'Property Way Evolution Price Detail'
    
    property_way_evolution_price_id = fields.Many2one(
        comodel_name='property.way.evolution.price',
        string='Property Way Evolution Price Id'
    )        
    homes_sold = fields.Integer(
        string='Homes Sold'
    )
    month = fields.Integer(
        string='Month'
    )
    year = fields.Integer(
        string='Year'
    )
    average_surface_area = fields.Float( 
        string='Average Surface Area'
    )
    average_price_by_sqare_meter = fields.Float( 
        string='Average Price by Square Meter'
    )
    average_price = fields.Float( 
        string='Average Price'
    )
