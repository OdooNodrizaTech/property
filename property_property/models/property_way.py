# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyWay(models.Model):
    _name = 'property.way'
    _description = 'Property way'
        
    property_town_id = fields.Many2one(
        comodel_name='property.town',
        string='Property Town Id'
    )
    external_id = fields.Char(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
    )
    property_way_type_id = fields.Many2one(
        comodel_name='property.way.type',
        string='Property Way Type Id'
    )    
    postal_code = fields.Char(
        string='Postal Code'
    )
    latitude = fields.Char(
        string='Latitude'
    )
    longitude = fields.Char(
        string='Latitude'
    )
    full = fields.Boolean(
        string='Full'
    )
    date_last_check = fields.Date(
        string='Date Last Check'
    )        
    source = fields.Selection(
        selection=[
            ('bbva','BBVA')                                      
        ],
        string='Source',
        default='bbva'
    )
    total_numbers = fields.Integer(
        string='Total Numbers'
    )
    
    @api.one    
    def action_update_way(self):
        current_date = datetime.now()
        #return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        #distritopostal.way
        distritopostal_way_ids = self.env['distritopostal.way'].search([('property_way_id', '=', self.id)])
        if len(distritopostal_way_ids)>0:
            distritopostal_way_id = distritopostal_way_ids[0]
            #request            
            url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/'+str(self.property_town_id.property_municipality_id.property_state_id.external_id)+'/municipalities/'+str(self.property_town_id.property_municipality_id.external_id)+'/towns/'+str(self.property_town_id.external_id)+'/ways'
            payload = {
                '$filter': '(name=='+str(distritopostal_way_id.name.encode('utf-8'))+')'
            }                         
            response = requests.get(url, params=payload)
            if response.status_code==200:
                response_json = json.loads(response.text)                        
                if 'provinces' in response_json:
                    for province in response_json['provinces']:
                        if 'municipalities' in province:
                            for municipality in province['municipalities']:
                                if 'towns' in municipality:
                                    for town in municipality['towns']:
                                        if 'ways' in town:
                                            for way in town['ways']:
                                                #latitude-longitude
                                                if 'location' in way:
                                                    location_value = way['location']['value'].replace(',', '.').split(';')
                                                    self.latitude = str(location_value[1])
                                                    #longitude
                                                    self.longitude = str(location_value[0].replace('-.', '-0.'))                     
                #Sleep 1 second to prevent error (if request)
                time.sleep(1)
            else:
                _logger.info('status_code')
                _logger.info(response.status_code)                                            
        #update date_last_check
        self.date_last_check = current_date.strftime("%Y-%m-%d")
        #return
        return return_item
    
    @api.one    
    def action_get_numbers(self):
        current_date = datetime.now()
        #return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        #requests
        total_numbers = 0
        url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/'+str(self.property_town_id.property_municipality_id.property_state_id.external_id)+'/municipalities/'+str(self.property_town_id.property_municipality_id.external_id)+'/ways/'+str(self.external_id)+'/numbers'
        response = requests.get(url)                                             
        if response.status_code==200:
            response_json = json.loads(response.text)
            #operations
            if 'provinces' in response_json:
                for province in response_json['provinces']:
                    if province['id']==self.property_town_id.property_municipality_id.property_state_id.external_id:
                        if 'municipalities' in province:
                            for municipality in province['municipalities']:
                                if 'towns' in municipality:
                                    for town in municipality['towns']:
                                        if 'ways' in town:
                                            for way in town['ways']:
                                                if str(way['id'])==self.external_id:
                                                    if 'numbers' in way:
                                                        for number in way['numbers']:
                                                            property_number_ids = self.env['property.number'].search(
                                                                [
                                                                    ('property_way_id', '=', self.id),
                                                                    ('external_id', '=', str(number['id']))
                                                                ]
                                                            )
                                                            if len(property_number_ids)==0:
                                                                #creamos
                                                                property_number_vals = {
                                                                    'property_way_id': self.id,                                                    
                                                                    'external_id': str(number['id']),
                                                                    'source': 'bbva'
                                                                }
                                                                #latitude-longitude
                                                                if 'name' in number:
                                                                    property_number_vals['name'] = str(number['name'].encode('utf-8'))
                                                                #create
                                                                property_number_obj = self.env['property.number'].sudo().create(property_number_vals)
                                                                #total_numbers
                                                                total_numbers += 1
        else:
            _logger.info('status_code')
            _logger.info(response.status_code)
            _logger.info(url)        
        #update date_last_check + total_numbers
        self.date_last_check = current_date.strftime("%Y-%m-%d")
        self.total_numbers = total_numbers                                                                
        #return
        return return_item        
    
    @api.multi    
    def cron_check_ways(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_ways')
        
        property_municipality_ids = self.env['property.municipality'].search([('full_ways', '=', False)])
        if len(property_municipality_ids)>0:
            count = 0
            for property_municipality_id in property_municipality_ids:
                count += 1
                #action_get_ways
                return_item = property_municipality_id.action_get_ways()[0]
                if 'errors' in return_item:
                    if return_item['errors']==True:
                        _logger.info(return_item)
                        #fix
                        if return_item['status_code']!=403:
                            _logger.info(paramos)
                        else:
                            _logger.info('Raro que sea un 403 pero pasamos')
                #_logger                
                percent = (float(count)/float(len(property_municipality_ids)))*100
                percent = "{0:.2f}".format(percent)                    
                _logger.info(str(property_municipality_id.name.encode('utf-8'))+' - '+str(percent)+'% ('+str(count)+'/'+str(len(property_municipality_ids))+')')                                        
                #update
                property_municipality_id.full_ways = True
                
    @api.multi    
    def cron_update_ways(self, cr=None, uid=False, context=None):
        _logger.info('cron_update_ways')
        
        property_way_ids = self.env['property.way'].search([('full', '=', True)])
        if len(property_way_ids)>0:
            count = 0
            for property_way_id in property_way_ids:
                count += 1
                #action_get_municipalities
                return_item = property_way_id.action_update_way()[0]
                if 'errors' in return_item:
                    if return_item['errors']==True:
                        _logger.info(return_item)
                        #fix
                        if return_item['status_code']!=403:
                            _logger.info(paramos)
                        else:
                            _logger.info('Raro que sea un 403 pero pasamos')
                #_logger                
                percent = (float(count)/float(len(property_way_ids)))*100
                percent = "{0:.2f}".format(percent)                    
                _logger.info(str(property_way_id.id)+' - '+str(percent)+'% ('+str(count)+'/'+str(len(property_way_ids))+')')         