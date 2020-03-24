# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class DistritopostalState(models.Model):
    _name = 'distritopostal.state'
    _description = 'Distritopostal State'
    
    name = fields.Char(
        string='Name'
    )
    url = fields.Char(
        string='Url'
    )