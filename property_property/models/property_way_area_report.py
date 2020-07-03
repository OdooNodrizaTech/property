# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyWayAreaReport(models.Model):
    _name = 'property.way.area.report'
    _description = 'Property Way Area Report'

    property_way_id = fields.Many2one(
        comodel_name='property.way',
        string='Property Way Id'
    )
    property_transaction_type_id = fields.Many2one(
        comodel_name='property.transaction.type',
        string='Property Transaction Type Id'
    )
    radius = fields.Integer(
        string='Radius'
    )
    total = fields.Integer(
        string='Total'
    )
    average_value = fields.Float(
        string='Avetage Value'
    )
    average_surface_area = fields.Float(
        string='Avetage Surface Area'
    )
    percentage = fields.Float(
        string='Percentage'
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
    def action_check(self, tsec):
        current_date = datetime.now()
        #return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        #requests
        url = 'https://www.bbva.es/ASO/financialPropertyInformation/V01/getPropertyAreaReport/'
        body_obj = {
            "location":{
                "latitude": str(self.property_way_id.latitude),                    
                "longitude": str(self.property_way_id.longitude)                
            },
            "radius": self.radius,
            "operationType":{
                "id": str(self.property_transaction_type_id.external_id)
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
            if 'flatReport' in response_json:
                #total
                if 'total' in response_json['flatReport']:
                    self.total = response_json['flatReport']['total']
                #averageValue
                if 'averageValue' in response_json['flatReport']:
                    if 'amount' in response_json['flatReport']['averageValue']:
                        self.average_value = response_json['flatReport']['averageValue']['amount']
                #averageSurfaceArea
                if 'averageSurfaceArea' in response_json['flatReport']:
                    self.average_surface_area = response_json['flatReport']['averageSurfaceArea']
                #percentage
                if 'percentage' in response_json['flatReport']:
                    self.percentage = response_json['flatReport']['percentage']
                #bedroomsReport
                if 'bedroomsReport' in response_json['flatReport']:
                    if len(response_json['flatReport']['bedroomsReport'])>0:
                        for bedrooms_report_item in response_json['flatReport']['bedroomsReport']:
                            if 'bedroomsNumber' in bedrooms_report_item:
                                #beedroom_number
                                beedroom_number = int(bedrooms_report_item['bedroomsNumber'])
                                #search
                                property_way_area_report_detail_ids = self.env['property.way.area.report.detail'].search(
                                    [
                                        ('property_way_area_report_id', '=', self.id),
                                        ('beedroom_number', '=', beedroom_number)
                                    ]
                                )
                                if len(property_way_area_report_detail_ids)==0:
                                    #vals
                                    property_way_area_report_detail_vals = {
                                        'property_way_area_report_id': self.id,
                                        'beedroom_number': beedroom_number
                                    }
                                    #averageSurfaceArea
                                    if 'averageSurfaceArea' in bedrooms_report_item:
                                        property_way_area_report_detail_vals['average_surface'] = bedrooms_report_item['averageSurfaceArea']
                                    #averagePrice
                                    if 'averagePrice' in bedrooms_report_item:
                                        if 'amount' in bedrooms_report_item['averagePrice']:
                                            property_way_area_report_detail_vals['average_price'] = bedrooms_report_item['averagePrice']['amount']
                                    #percentage
                                    if 'percentage' in bedrooms_report_item:
                                        property_way_area_report_detail_vals['percentage'] = bedrooms_report_item['percentage']
                                    #create
                                    property_way_area_report_detail_obj = self.env['property.way.area.report.detail'].sudo().create(property_way_area_report_detail_vals)                                
        #update date_last_check + total_build_units
        self.date_last_check = current_date.strftime("%Y-%m-%d")            
        #return
        return return_item                                                    
    
    @api.multi    
    def cron_check_ways_area_report(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_ways_area_report')
        
        property_transaction_type_ids = self.env['property.transaction.type'].search([('id', '>', 0)])
        if len(property_transaction_type_ids)>0:
            for property_transaction_type_id in property_transaction_type_ids:        
                property_way_area_report_ids = self.env['property.way.area.report'].search([('property_transaction_type_id', '=', property_transaction_type_id.id)])
                if len(property_way_area_report_ids)>0:
                    property_way_ids = self.env['property.way'].search(
                        [
                            ('id', 'not in', property_way_area_report_ids.mapped('property_way_id').ids),
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
                        property_way_area_report_vals = {
                            'property_way_id': property_way_id.id,
                            'property_transaction_type_id': property_transaction_type_id.id,
                            'radius': 1000,
                            'source': 'bbva'
                        }                
                        property_way_area_report_obj = self.env['property.way.area.report'].sudo().create(property_way_area_report_vals)                
        #now check all property.way.area.report
        property_way_area_report_ids = self.env['property.way.area.report'].search([('full', '=', False)], limit=2000)
        if len(property_way_area_report_ids)>0:
            count = 0
            #generate_tsec
            tsec = self.bbva_generate_tsec()
            if tsec!=False:            
                for property_way_area_report_id in property_way_area_report_ids:
                    count += 1
                    #action_check
                    return_item = property_way_area_report_id.action_check(tsec)[0]
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
                    percent = (float(count)/float(len(property_way_area_report_ids)))*100
                    percent = "{0:.2f}".format(percent)                    
                    _logger.info(str(property_way_area_report_id.id)+' - '+str(percent)+'% ('+str(count)+'/'+str(len(property_way_area_report_ids))+')')                                        
                    #update
                    if return_item['status_code']!=403:
                        property_way_area_report_id.full = True
                    #Sleep 1 second to prevent error (if request)
                    time.sleep(1)