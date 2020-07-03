# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyUse(models.Model):
    _name = 'property.use'
    _description = 'Property Use'
    
    external_id = fields.Char(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
    )        