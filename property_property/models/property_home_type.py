# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyHomeType(models.Model):
    _name = 'property.home.type'
    _description = 'Property Home Type'
    
    external_id = fields.Char(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
    )