# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyProperty(models.Model):
    _name = 'property.property'
    _description = 'Property Property'
    
    property_number_id = fields.Many2one(
        comodel_name='property.number',
        string='Property Number Id'
    )
    external_id = fields.Char(
        string='External Id'
    )
    surface_area = fields.Integer(
        string='Surface Area'
    )
    plot_surface_area = fields.Integer(
        string='Plot Surface Area'
    )
    built_surface_area = fields.Integer(
        string='Built Surface Area'
    )
    coefficient = fields.Float(
        string='Coefficient'
    )
    property_use_id = fields.Many2one(
        comodel_name='property.use',
        string='Property Use Id'
    )
    property_building_type_id = fields.Many2one(
        comodel_name='property.building.type',
        string='Property Building Type Id'
    )
    year_old = fields.Integer(
        string='Year Old'
    )
    building_year = fields.Integer(
        string='Building Year'
    )
    reform_year = fields.Integer(
        string='Reform Year'
    )
    plot_registry_id = fields.Char(
        string='Plot Registry Id'
    )
    stair = fields.Char(
        string='Stair'
    )
    floor = fields.Char(
        string='Floor'
    )
    door = fields.Char(
        string='Door'
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
    total_build_units = fields.Integer(
        string='Total Build Units'
    )        
    
    @api.multi    
    def bbva_generate_tsec(self):
        tsec = False
        url = 'https://www.bbva.es/ASO/TechArchitecture/grantingTicketsOauth/V01/'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic '+str(self.env['ir.config_parameter'].sudo().get_param('bbva_authorization_key'))
        }
        data_obj = {
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, headers=headers, data=data_obj)
        if response.status_code==200:        
            response_json = json.loads(response.text)        
            if 'access_token' in response_json:
                tsec = str(response_json['access_token'])
            
        return tsec            
        
    @api.one    
    def action_get_full_info(self, tsec, property_use_id_external_id=False):
        current_date = datetime.now()
        #return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        #property_use_id_external_id
        if property_use_id_external_id==False:
            property_use_id_external_id = []
            property_use_ids = self.env['property.use'].search([('id', '>', 0)])
            if len(property_use_ids)>0:
                for property_use_id in property_use_ids:
                    property_use_id_external_id[str(property_use_id.external_id)] = property_use_id.id
        #requests
        total_build_units = 0
        url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/'+str(self.property_number_id.property_way_id.property_town_id.property_municipality_id.property_state_id.external_id)+'/municipalities/'+str(self.property_number_id.property_way_id.property_town_id.property_municipality_id.external_id)+'/towns/'+str(self.property_number_id.property_way_id.property_town_id.external_id)+'/ways/'+str(self.property_number_id.property_way_id.external_id)+'/numbers/'+str(self.property_number_id.external_id)+'/properties/'+str(self.external_id)
        headers={'tsec': str(tsec)}
        response = requests.get(url, headers=headers)        
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
                                            if 'numbers' in way:
                                                for number in way['numbers']:
                                                    if 'properties' in number:
                                                        for property in number['properties']:                                                            
                                                            #stair
                                                            if 'stair' in property:
                                                                self.stair = str(property['stair'])
                                                            #floor
                                                            if 'floor' in property:
                                                                self.floor = str(property['floor'])
                                                            #door
                                                            if 'door' in property:
                                                                self.door = str(property['door'])
                                                            #buildUnits
                                                            if 'buildUnits' in property:
                                                                for build_unit in property['buildUnits']:
                                                                    if 'id' in build_unit:
                                                                        property_property_build_unit_ids = self.env['property.property.build.unit'].search(
                                                                            [
                                                                                ('property_property_id', '=', self.id),
                                                                                ('external_id', '=', str(build_unit['id']))
                                                                            ]
                                                                        )
                                                                        if len(property_property_build_unit_ids)>0:
                                                                            #vals
                                                                            property_property_build_unit_vals = {
                                                                                'property_property_id': self.id,
                                                                                'external_id': str(build_unit['id']),
                                                                                'source': 'bbva'
                                                                            }                                                                    
                                                                            #stair
                                                                            if 'stair' in build_unit:
                                                                                property_property_build_unit_vals['stair'] = str(build_unit['stair'])
                                                                            #floor
                                                                            if 'floor'in build_unit:
                                                                                property_property_build_unit_vals['floor'] = str(build_unit['floor'])
                                                                            #door
                                                                            if 'door' in build_unit:
                                                                                property_property_build_unit_vals['door'] = str(build_unit['door'])
                                                                            #builtSurfaceArea
                                                                            if 'builtSurfaceArea' in build_unit:
                                                                                property_property_build_unit_vals['built_surface_area'] = int(build_unit['builtSurfaceArea'])
                                                                            #useCode
                                                                            if 'useCode' in build_unit:
                                                                                if 'id' in build_unit['useCode']:
                                                                                    if str(build_unit['useCode']['id']) in property_use_id_external_id:
                                                                                        property_property_build_unit_vals['property_use_id'] = int(property_use_id_external_id[str(build_unit['useCode']['id'])])
                                                                            #create
                                                                            property_property_build_unit_obj = self.env['property.property.build.unit'].sudo().create(property_property_build_unit_vals)
                                                                            #total_build_units
                                                                            total_build_units += 1
        else:
            _logger.info('status_code')
            _logger.info(response.status_code)
            _logger.info(url)
        #update date_last_check + total_build_units
        self.date_last_check = current_date.strftime("%Y-%m-%d")
        self.total_build_units = total_build_units            
        #return
        return return_item
    
    @api.multi    
    def cron_check_properties(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_properties')
        
        property_number_ids = self.env['property.number'].search([('full', '=', False)], limit=3000)
        if len(property_number_ids)>0:
            count = 0
            #generate_tsec
            tsec = self.bbva_generate_tsec()
            if tsec!=False:
                #property_user_id_external_id (optimize multi-query)
                property_user_id_external_id = {}
                property_use_ids = self.env['property.use'].search([('id', '>', 0)])
                if len(property_use_ids)>0:
                    for property_use_id in property_use_ids:
                        property_user_id_external_id[str(property_use_id.external_id)] = property_use_id.id            
                #property_building_type_id_external_id (optimize multi-query)
                property_building_type_id_external_id = {}
                property_building_type_ids = self.env['property.building.type'].search([('id', '>', 0)])
                if len(property_building_type_ids)>0:
                    for property_building_type_id in property_building_type_ids:
                        property_building_type_id_external_id[str(property_building_type_id.external_id)] = property_building_type_id.id
                #for
                for property_number_id in property_number_ids:
                    count += 1
                    #action_get_properties
                    return_item = property_number_id.action_get_properties(tsec, property_user_id_external_id, property_building_type_id_external_id)[0]
                    if 'errors' in return_item:
                        if return_item['errors']==True:
                            _logger.info(return_item)
                            #fix
                            if return_item['status_code']!=403:
                                _logger.info(paramos)
                            else:
                                _logger.info('Raro que sea un 403 pero pasamos')
                                #generamos de nuevo el tsecs
                                tsec = self.bbva_generate_tsec()
                    #_logger                
                    percent = (float(count)/float(len(property_number_ids)))*100
                    percent = "{0:.2f}".format(percent)                    
                    _logger.info(str(property_number_id.id)+' - '+str(percent)+'% ('+str(count)+'/'+str(len(property_number_ids))+')')                                        
                    #update
                    if return_item['status_code']!=403:
                        property_number_id.full = True  
                    #Sleep 1 second to prevent error (if request)
                    time.sleep(1)
                    
    @api.multi    
    def cron_check_properties_full_info(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_properties_full_info')
        
        property_property_ids = self.env['property.property'].search([('full', '=', False)], limit=3000)
        if len(property_property_ids)>0:
            #generate_tsec
            tsec = self.bbva_generate_tsec()
            if tsec!=False:
                count = 0
                #property_use_id_name (optimize multi-query)
                property_use_id_external_id = {}
                property_use_ids = self.env['property.use'].search([('id', '>', 0)])
                if len(property_use_ids)>0:
                    for property_use_id in property_use_ids:
                        property_use_id_external_id[str(property_use_id.external_id)] = property_use_id.id
                #for
                for property_property_id in property_property_ids:                
                    count += 1
                    #action_get_full_info
                    return_item = property_property_id.action_get_full_info(tsec, property_use_id_external_id)[0]
                    if 'errors' in return_item:
                        if return_item['errors']==True:
                            _logger.info(return_item)
                            #fix
                            if return_item['status_code']!=403:
                                _logger.info(paramos)
                            else:
                                _logger.info('Raro que sea un 403 pero pasamos')
                                #generamos de nuevo el tsecs
                                tsec = self.bbva_generate_tsec()
                    #_logger                
                    percent = (float(count)/float(len(property_property_ids)))*100
                    percent = "{0:.2f}".format(percent)                    
                    _logger.info(str(property_property_id.external_id)+' - '+str(percent)+'% ('+str(count)+'/'+str(len(property_property_ids))+')')                                        
                    #update
                    if return_item['status_code']==200:
                        property_property_id.full = True  
                    #Sleep 1 second to prevent error (if request)
                    time.sleep(1)