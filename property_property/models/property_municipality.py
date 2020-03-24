# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyMunicipality(models.Model):
    _name = 'property.municipality'
    _description = 'Property Municipality'
    
    property_state_id = fields.Many2one(
        comodel_name='property.state',
        string='Property State Id'
    )
    external_id = fields.Char(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
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
    full_ways = fields.Boolean(
        string='Full full_ways'
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
    total_towns = fields.Integer(
        string='Total towns'
    )
    total_ways = fields.Integer(
        string='Total Ways'
    )
    
    @api.one    
    def action_update_municipality(self):
        current_date = datetime.now()
        #return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        #distritopostal.municipality
        distritopostal_municipality_ids = self.env['distritopostal.municipality'].search([('property_municipality_id', '=', self.id)])
        if len(distritopostal_municipality_ids)>0:
            distritopostal_municipality_id = distritopostal_municipality_ids[0]
            #request            
            url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/'+str(self.external_id)+'/municipalities/'
            payload = {
                '$filter': '(name=='+str(distritopostal_municipality_id.name.encode('utf-8'))+')'
            }                         
            response = requests.get(url, params=payload)                    
            if response.status_code==200:
                response_json = json.loads(response.text)
                if 'provinces' in response_json:
                    for province in response_json['provinces']:
                        if 'municipalities' in province:
                            for municipality in province['municipalities']: 
                                if 'location' in municipality:
                                    if 'value' in municipality['location']:
                                        location_value = municipality['location']['value'].replace(',', '.').split(';')
                                        self.latitude = str(location_value[1])
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
    def action_get_towns(self):
        current_date = datetime.now()
        #return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        #operations
        total_towns = 0
        url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/'+str(self.property_state_id.external_id)+'/municipalities/'+str(self.external_id)+'/towns'
        response = requests.get(url)
        if response.status_code==200:
            response_json = json.loads(response.text)
            if 'provinces' in response_json:
                for province in response_json['provinces']:
                    if 'municipalities' in province:
                        for municipality in province['municipalities']:
                            if 'towns' in municipality:
                                for town in municipality['towns']:
                                    property_town_ids = self.env['property.town'].search(
                                        [
                                            ('property_municipality_id', '=', self.id),
                                            ('external_id', '=', str(town['id']))
                                        ]
                                    )
                                    if len(property_town_ids)==0:
                                        #creamos
                                        property_town_vals = {
                                            'property_municipality_id': self.id,                                                    
                                            'external_id': str(town['id']),
                                            'name': str(town['name'].encode('utf-8')),
                                            'source': 'bbva'
                                        }
                                        property_town_obj = self.env['property.town'].sudo().create(property_town_vals)
                                        #total_towns
                                        total_towns += 1                                        
        else:
            _logger.info('status_code')
            _logger.info(response.status_code)
        #update date_last_check
        self.date_last_check = current_date.strftime("%Y-%m-%d")
        self.total_towns = total_towns
        #return
        return return_item                                
    
    @api.multi    
    def cron_check_municipalities(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_municipalities')
        
        property_state_ids = self.env['property.state'].search([('full', '=', False)])
        if len(property_state_ids)>0:
            count = 0
            for property_state_id in property_state_ids:
                count += 1
                #action_get_municipalities
                return_item = property_state_id.action_get_municipalities()[0]
                if 'errors' in return_item:
                    if return_item['errors']==True:
                        _logger.info(return_item)
                        #fix
                        if return_item['status_code']!=403:
                            _logger.info(paramos)
                        else:
                            _logger.info('Raro que sea un 403 pero pasamos')
                #_logger                
                percent = (float(count)/float(len(property_state_ids)))*100
                percent = "{0:.2f}".format(percent)                    
                _logger.info(str(property_state_id.id)+' - '+str(percent)+'% ('+str(count)+'/'+str(len(property_state_ids))+')')
                #update
                property_state_id.full = True
                #Sleep 1 second to prevent error (if request)
                time.sleep(1)
    
    @api.multi    
    def cron_update_municipalities(self, cr=None, uid=False, context=None):
        _logger.info('cron_update_municipalities')
        
        property_municipality_ids = self.env['property.municipality'].search([('full', '=', True)])
        if len(property_municipality_ids)>0:
            count = 0
            for property_municipality_id in property_municipality_ids:
                count += 1
                #action_update_municipality
                return_item = property_municipality_id.action_update_municipality()[0]
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
                _logger.info(str(property_municipality_id.id)+' - '+str(percent)+'% ('+str(count)+'/'+str(len(property_municipality_ids))+')')
                
    @api.one    
    def action_get_ways(self):
        current_date = datetime.now()
        #return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        total_ways = 0
        #distritopostal.municipality
        distritopostal_municipality_ids = self.env['distritopostal.municipality'].search([('property_municipality_id', '=', self.id)])
        if len(distritopostal_municipality_ids)>0:
            distritopostal_municipality_id = distritopostal_municipality_ids[0]
            distritopostal_way_ids = self.env['distritopostal.way'].search([('distritopostal_municipality_id', '=', distritopostal_municipality_id.id)])
            if len(distritopostal_way_ids)>0:
                count = 0
                for distritopostal_way_id in distritopostal_way_ids:
                    count += 1                    
                    #_logger                
                    percent = (float(count)/float(len(distritopostal_way_ids)))*100
                    percent = "{0:.2f}".format(percent)                    
                    _logger.info(str(distritopostal_way_id.id)+' - '+str(percent)+'% ('+str(count)+'/'+str(len(distritopostal_way_ids))+')')
                    #request            
                    url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/'+str(self.property_state_id.external_id)+'/municipalities/'+str(self.external_id)+'/ways'
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
                                                if 'id' in town:
                                                    property_town_ids = self.env['property.town'].search(
                                                        [
                                                            ('property_municipality_id', '=', self.id),
                                                            ('external_id', '=', str(town['id']))
                                                        ]
                                                    )
                                                    if len(property_town_ids)>0:
                                                        property_town_id = property_town_ids[0]
                                                        #ways                                                    
                                                        if 'ways' in town:
                                                            for way in town['ways']:
                                                                property_way_ids = self.env['property.way'].search(
                                                                    [
                                                                        ('property_town_id', '=', self.id),
                                                                        ('external_id', '=', str(way['id']))
                                                                    ]
                                                                )
                                                                if len(property_way_ids)==0:                                                                    
                                                                    #creamos
                                                                    property_way_vals = {
                                                                        'property_town_id': property_town_id.id,                                                    
                                                                        'external_id': str(way['id']),
                                                                        'name': str(way['name'].encode('utf-8')),
                                                                        'source': 'bbva'
                                                                    }
                                                                    #postalCode
                                                                    if 'postalCode' in way:
                                                                        property_way_vals['postal_code'] = str(way['postalCode'])
                                                                    #type
                                                                    if 'type' in way:
                                                                        if 'id' in way['type']:
                                                                            property_way_type_ids = self.env['property.way.type'].search(
                                                                                [
                                                                                    ('source', '=', 'bbva'),
                                                                                    ('external_id', '=', str(way['type']['id']))
                                                                                ]
                                                                            )
                                                                            if len(property_way_type_ids)>0:
                                                                                property_way_type_id = property_way_type_ids[0]
                                                                                property_way_vals['property_way_type_id'] = property_way_type_id.id
                                                                    #latitude-longitude
                                                                    if 'location' in way:
                                                                        location_value = way['location']['value'].replace(',', '.').split(';')
                                                                        property_way_vals['latitude'] = str(location_value[1])
                                                                        property_way_vals['longitude'] = str(location_value[0].replace('-.', '-0.'))
                                                                    #create
                                                                    property_way_obj = self.env['property.way'].sudo().create(property_way_vals)
                                                                    #distritopostal_way_id
                                                                    distritopostal_way_id.property_way_id = property_way_obj.id
                                                                    #total_ways
                                                                    total_ways += 1                        
                        #Sleep 1 second to prevent error (if request)
                        time.sleep(1)
                    else:
                        _logger.info('status_code')
                        _logger.info(response.status_code)                                            
            #update date_last_check
            self.date_last_check = current_date.strftime("%Y-%m-%d")
            self.total_ways = total_ways            
        #return
        return return_item
    
    @api.multi    
    def cron_check_ways(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_ways')
        
        property_municipality_ids = self.env['property.municipality'].search([('full_ways', '=', False)])
        if len(property_municipality_ids)>0:
            count = 0
            for property_municipality_id in property_municipality_ids:
                property_town_ids = self.env['property.town'].search([('property_municipality_id', '=', property_municipality_id.id)])
                if len(property_town_ids)>0:#suponemos que si tiene 1 o + ya estan importados            
                    count += 1
                    #action_get_municipalities
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