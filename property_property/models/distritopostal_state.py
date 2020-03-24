# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

class DistritopostalState(models.Model):
    _inherit = 'distritopostal.state'
    
    property_state_id = fields.Many2one(
        comodel_name='property.state',
        string='Property State'
    )