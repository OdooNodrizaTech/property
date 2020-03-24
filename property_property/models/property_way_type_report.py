# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyWayTypeReport(models.Model):
    _name = 'property.way.type.report'
    _description = 'Property Way Type Report'
    
    property_way_id = fields.Many2one(
        comodel_name='property.way',
        string='Property Way Id'
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
    
    @api.multi    
    def bbva_generate_tsec(self):
        tsec = False
        url = 'https://www.bbva.es/ASO/TechArchitecture/grantingTicketsOauth/V01/'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic SU1NQjAwMTpTajhCbGpRYw=='
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
    def action_check(self, tsec):
        current_date = datetime.now()
        #return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        #requests
        url = 'https://www.bbva.es/ASO/financialPropertyInformation/V01/getPropertyTypeReport/'
        body_obj = {
            "location":{
                "latitude": str(self.property_way_id.latitude),                    
                "longitude": str(self.property_way_id.longitude)                
            }            
        } 
        headers = {
            'content-type': 'application/json',
            'tsec': str(tsec)
        }
        _logger.info(self.property_way_id.id)
        response = requests.post(url, headers=headers, data=json.dumps(body_obj))        
        if response.status_code==200:
            response_json = json.loads(response.text)
            if 'levelDistribution' in response_json:
                if len(response_json['levelDistribution'])>0:
                    for level_distribution_item in response_json['levelDistribution']:
                        if 'level' in level_distribution_item:
                            if 'id' in level_distribution_item['level']:
                                property_level_ids = self.env['property.level'].search([('external_id', '=', str(level_distribution_item['level']['id']))])
                                if len(property_level_ids)>0:
                                    property_level_id = property_level_ids[0]
                                    #vals
                                    property_way_type_report_detail_vals = {
                                        'property_way_type_report_id': self.id,
                                        'property_level_id': property_level_id.id
                                    }
                                    #search
                                    property_way_type_report_detail_ids = self.env['property.way.type.report.detail'].search(
                                        [
                                            ('property_way_type_report_id', '=', self.id),
                                            ('property_level_id', '=', property_way_type_report_detail_vals['property_level_id'])
                                        ]
                                    )
                                    if len(property_way_type_report_detail_ids)==0:
                                        #name
                                        if 'name' in level_distribution_item:
                                            property_way_type_report_detail_vals['name'] = str(level_distribution_item['name'])
                                        #flatDistribution
                                        if 'flatDistribution' in level_distribution_item:
                                            #freeOffer
                                            if 'freeOffer' in level_distribution_item['flatDistribution']:
                                                property_way_type_report_detail_vals['flat_distribution_free_offer'] = level_distribution_item['flatDistribution']['freeOffer']
                                            #bankOffer
                                            if 'bankOffer' in level_distribution_item['flatDistribution']:
                                                property_way_type_report_detail_vals['flat_distribution_bank_offer'] = level_distribution_item['flatDistribution']['bankOffer']
                                            #total
                                            if 'total' in level_distribution_item['flatDistribution']:
                                                property_way_type_report_detail_vals['flat_distribution_total'] = level_distribution_item['flatDistribution']['total']
                                        #detachedPropertyDistribution
                                        if 'detachedPropertyDistribution' in level_distribution_item:
                                            #freeOffer
                                            if 'freeOffer' in level_distribution_item['detachedPropertyDistribution']:
                                                property_way_type_report_detail_vals['detached_property_distribution_free_offer'] = level_distribution_item['detachedPropertyDistribution']['freeOffer']
                                            #bankOffer
                                            if 'bankOffer' in level_distribution_item['detachedPropertyDistribution']:
                                                property_way_type_report_detail_vals['detached_property_distribution_bank_offer'] = level_distribution_item['detachedPropertyDistribution']['bankOffer']
                                            #total
                                            if 'total' in level_distribution_item['detachedPropertyDistribution']:
                                                property_way_type_report_detail_vals['detached_property_distribution_total'] = level_distribution_item['detachedPropertyDistribution']['total']
                                        #create
                                        property_way_type_report_detail_obj = self.env['property.way.type.report.detail'].sudo().create(property_way_type_report_detail_vals)
        #update date_last_check + total_build_units
        self.date_last_check = current_date.strftime("%Y-%m-%d")            
        #return
        return return_item                    
    
    @api.multi    
    def cron_check_ways_type_report(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_ways_type_report')
        
        property_way_type_report_ids = self.env['property.way.type.report'].search([('id', '>', 0)])
        if len(property_way_type_report_ids)>0:
            property_way_ids = self.env['property.way'].search(
                [
                    ('id', 'not in', property_way_type_report_ids.mapped('property_way_id').ids),
                    ('latitude', '!=', False),
                    ('longitude', '!=', False)
                ]
            )
        else:
            property_way_ids = self.env['property.way'].search(
                [
                    ('latitude', '!=', False),
                    ('longitude', '!=', False)
                ]
            )
        #operations-generate
        if len(property_way_ids)>0:
            for property_way_id in property_way_ids:
                #cals
                property_way_type_report_vals = {
                    'property_way_id': property_way_id.id,
                    'source': 'bbva'
                }                
                property_way_type_report_obj = self.env['property.way.type.report'].sudo().create(property_way_type_report_vals)                
        #now check all property.way.type.report
        property_way_type_report_ids = self.env['property.way.type.report'].search([('full', '=', False)], limit=2000)
        if len(property_way_type_report_ids)>0:
            count = 0
            #generate_tsec
            tsec = self.bbva_generate_tsec()
            if tsec!=False:            
                for property_way_type_report_id in property_way_type_report_ids:
                    count += 1
                    #action_check
                    return_item = property_way_type_report_id.action_check(tsec)[0]
                    if 'errors' in return_item:
                        if return_item['errors']==True:
                            _logger.info(return_item)
                            #fix
                            if return_item['status_code']!=403:
                                _logger.info(paramos)
                            else:
                                _logger.info('Raro que sea un 403 pero pasamos')
                                tsec = self.bbva_generate_tsec()
                    #_logger                
                    percent = (float(count)/float(len(property_way_type_report_ids)))*100
                    percent = "{0:.2f}".format(percent)                    
                    _logger.info(str(property_way_type_report_id.id)+' - '+str(percent)+'% ('+str(count)+'/'+str(len(property_way_type_report_ids))+')')                                        
                    #update
                    if return_item['status_code']!=403:
                        property_way_type_report_id.full = True
                    #Sleep 1 second to prevent error (if request)
                    time.sleep(1)                                        