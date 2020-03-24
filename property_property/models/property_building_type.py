# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyBuildingType(models.Model):
    _name = 'property.building.type'
    _description = 'Property Building Type'
    
    external_id = fields.Char(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
    )