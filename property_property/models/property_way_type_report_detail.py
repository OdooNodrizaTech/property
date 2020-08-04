# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PropertyWayTypeReportDetail(models.Model):
    _name = 'property.way.type.report.detail'
    _description = 'Property Way Type Report Detail'
    
    property_way_type_report_id = fields.Many2one(
        comodel_name='property.way.type.report',
        string='Property Way Type Report Id'
    )
    property_level_id = fields.Many2one(
        comodel_name='property.level',
        string='Property Level Id'
    )                    
    name = fields.Char(
        string='Name'
    )
    flat_distribution_free_offer = fields.Integer(
        string='Flat Distribution Free Offer'
    )
    flat_distribution_bank_offer = fields.Integer(
        string='Flat Distribution Bank Offer'
    )
    flat_distribution_total = fields.Integer(
        string='Flat Distribution Total'
    )
    detached_property_distribution_free_offer = fields.Integer(
        string='Detached Property Distribution Free Offer'
    )
    detached_property_distribution_bank_offer = fields.Integer(
        string='Detached Property Distribution Bank Offer'
    )
    detached_property_distribution_total = fields.Integer(
        string='Detached Property Distribution Total'
    )
