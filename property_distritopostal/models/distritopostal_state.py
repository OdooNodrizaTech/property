# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DistritopostalState(models.Model):
    _name = 'distritopostal.state'
    _description = 'Distritopostal State'
    
    name = fields.Char(
        string='Name'
    )
    url = fields.Char(
        string='Url'
    )