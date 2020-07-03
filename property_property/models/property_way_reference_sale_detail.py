# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyWayReferenceSaleDetail(models.Model):
    _name = 'property.way.reference.sale.detail'
    _description = 'Property Way Reference Sale Detail'
    
    property_way_reference_sale_id = fields.Many2one(
        comodel_name='property.way.reference.sale',
        string='Property Way Reference Sale Id'
    )
    description = fields.Char(
        string='Description'
    )
    price = fields.Float(
        string='Price'
    )
    surface_area = fields.Float(
        string='Surface Area'
    )
    bedrooms_number = fields.Integer(
        string='Bedrooms Number'
    )
    toilets_number = fields.Integer(
        string='Toilets Number'
    )
    latitude = fields.Char(
        string='Latitude'
    )
    longitude = fields.Char(
        string='Latitude'
    )
    url_image = fields.Char(
        string='Url Image'
    )
    url_detail = fields.Char(
        string='Url Detail'
    )
    average_price_surface_area = fields.Float(
        string='Average Price Surface Area'
    )    