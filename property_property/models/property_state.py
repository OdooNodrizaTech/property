# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyState(models.Model):
    _name = 'property.state'
    _description = 'Property State'
    
    external_id = fields.Char(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
    )
    latitude = fields.Float(
        string='Latitude'
    )
    longitude = fields.Float(
        string='Latitude'
    )
    full = fields.Boolean(
        string='Full'
    )
    date_last_check = fields.Date(
        string='Date Last Check'
    )
    res_country_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Res Country State Id'
    )    
    source = fields.Selection(
        selection=[
            ('bbva','BBVA')                                      
        ],
        string='Source',
        default='bbva'
    )
    total_municipalities = fields.Integer(
        string='Total municipalities'
    )
    
    @api.one    
    def action_get_municipalities(self):
        current_date = datetime.now()
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # distritopostal.state
        distritopostal_state_ids = self.env['distritopostal.state'].search(
            [
                ('property_state_id', '=', self.id)
            ]
        )
        if distritopostal_state_ids:
            distritopostal_state_id = distritopostal_state_ids[0]
            distritopostal_municipality_ids = self.env['distritopostal.municipality'].search(
                [
                    ('distritopostal_state_id', '=', distritopostal_state_id.id)
                ]
            )
            # operations
            if distritopostal_municipality_ids:
                count = 0            
                for distritopostal_municipality_id in distritopostal_municipality_ids:
                    count += 1
                    # _logger
                    percent = (float(count)/float(len(distritopostal_municipality_ids)))*100
                    percent = "{0:.2f}".format(percent)
                    _logger.info('%s - %s%s (%s/%s)' % (
                        distritopostal_municipality_id.external_id,
                        percent,
                        '%',
                        count,
                        len(distritopostal_municipality_ids)
                    ))
                    # request
                    url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/%s/municipalities/' % self.external_id
                    payload = {
                        '$filter': '(name=='+str(distritopostal_municipality_id.name.encode('utf-8'))+')'
                    }                         
                    response = requests.get(url, params=payload)                    
                    if response.status_code == 200:
                        response_json = json.loads(response.text)
                        if 'provinces' in response_json:
                            for province in response_json['provinces']:
                                if 'municipalities' in province:
                                    for municipality in province['municipalities']:
                                        property_municipality_ids = self.env['property.municipality'].search(
                                            [
                                                ('property_state_id', '=', self.id),
                                                ('external_id', '=', str(municipality['id']))
                                            ]
                                        ) 
                                        if len(property_municipality_ids) == 0:
                                            # creamos
                                            vals = {
                                                'property_state_id': self.id,                                                                                                        
                                                'external_id': str(municipality['id']),
                                                'name': str(municipality['name'].encode('utf-8')),
                                                'source': 'bbva',
                                                'total_towns': 0
                                            }
                                            # location
                                            if 'location' in municipality:
                                                if 'value' in municipality['location']:
                                                    location_value = municipality['location']['value'].replace(',', '.').split(';')
                                                    # _logger.info(location_value)
                                                    vals['latitude'] = str(location_value[1])
                                                    vals['longitude'] = str(location_value[0].replace('-.', '-0.'))
                                            # create
                                            property_municipality_obj = self.env['property.municipality'].sudo().create(vals)
                                            # update
                                            distritopostal_municipality_id.property_municipality_id = property_municipality_obj.id                                             
                        # Sleep 1 second to prevent error (if request)
                        time.sleep(1)                                                                        
                    else:
                        _logger.info('status_code')
                        _logger.info(response.status_code)                    
            # update date_last_check
            self.date_last_check = current_date.strftime("%Y-%m-%d")                                                
        # return
        return return_item    
    
    @api.multi    
    def cron_check_states(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_states')
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # all_items
        property_state_external_id = []
        property_state_ids = self.env['property.state'].search([('id', '>', 0)])
        if property_state_ids:
            for property_state_id in property_state_ids:
                property_state_external_id.append(str(property_state_id.external_id))
        # requests
        url = 'https://www.bbva.es/ASO/streetMap/V02/provinces'
        response = requests.get(url=url)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if 'provinces' in response_json:
                for province in response_json['provinces']:
                    if str(province['id']) not in property_state_external_id:                            
                        # creamos
                        vals = {
                            'external_id': str(province['id']),
                            'name': str(province['name'].encode('utf-8')),
                            'source': 'bbva',
                            'total_municipalities': 0
                        }
                        # location
                        if 'location' in province:
                            if 'value' in province['location']:
                                location_value = province['location']['value'].split(';')
                                vals['latitude'] = str(location_value[0])
                                vals['longitude'] = str(location_value[1])
                        # create
                        self.env['property.state'].sudo().create(vals)
        else:
            return_item = {
                'errors': True,
                'status_code': response.status_code,
                'error': {                    
                    'url': url,
                    'text': response.text
                }
            }
        # return
        _logger.info(return_item)                                                                