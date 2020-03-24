# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyWayType(models.Model):
    _name = 'property.way.type'
    _description = 'Property way Type'
            
    external_id = fields.Char(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
    )            
    source = fields.Selection(
        selection=[
            ('bbva','BBVA')                                      
        ],
        string='Source',
        default='bbva'
    )            
    
    @api.multi    
    def cron_check_way_types(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_way_types')
        #requests                         
        url = 'https://www.bbva.es/ASO/streetMap/V02/wayTypes/'
        response = requests.get(url=url)
        if response.status_code==200:
            response_json = json.loads(response.text)
            if 'wayTypes' in response_json:
                if len(response_json['wayTypes'])>0:
                    for way_type in response_json['wayTypes']:
                        if 'id' in way_type:
                            property_way_type_ids = self.env['property.way.type'].search(
                                [
                                    ('source', '=', 'bbva'),
                                    ('external_id', '=', str(way_type['id']))
                                ]
                            )
                            if len(property_way_type_ids)==0:
                                #creamos
                                property_way_type_vals = {
                                    'external_id': str(way_type['id']),
                                    'name': str(way_type['name'].encode('utf-8')),
                                    'source': 'bbva'
                                }
                                #create
                                property_way_type_obj = self.env['property.way.type'].sudo().create(property_way_type_vals)                