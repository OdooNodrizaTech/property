# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PropertyWayAreaReportDetail(models.Model):
    _name = 'property.way.area.report.detail'
    _description = 'Property Way Area Report Detail'

    property_way_area_report_id = fields.Many2one(
        comodel_name='property.way.area.report',
        string='Property Way Area Report Id'
    )
    beedroom_number = fields.Integer(
        string='Beedroom Number'
    )
    average_surface = fields.Float(
        string='Avetage Surface'
    )
    average_price = fields.Float(
        string='Avetage Price'
    )
    percentage = fields.Float(
        string='Percentage'
    )
