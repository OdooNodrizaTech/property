# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

class DistritopostalMunicipality(models.Model):
    _inherit = 'distritopostal.municipality'
    
    property_municipality_id = fields.Many2one(
        comodel_name='property.municipality',
        string='Property Municipality'
    )