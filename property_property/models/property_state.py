# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models, _
import requests, xmltodict, json
from datetime import datetime
import pytz
import time
_logger = logging.getLogger(__name__)


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
            ('bbva', 'BBVA')
        ],
        string='Source',
        default='bbva'
    )
    total_municipalities = fields.Integer(
        string='Total municipalities'
    )
    
    @api.multi
    def action_get_municipalities(self):
        self.ensure_one
        current_date = datetime.now()
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # distritopostal.state
        state_ids = self.env['distritopostal.state'].search(
            [
                ('property_state_id', '=', self.id)
            ]
        )
        if state_ids:
            state_id = state_ids[0]
            municipality_ids = self.env['distritopostal.municipality'].search(
                [
                    ('distritopostal_state_id', '=', state_id.id)
                ]
            )
            # operations
            if municipality_ids:
                count = 0            
                for municipality_id in municipality_ids:
                    count += 1
                    # _logger
                    percent = (float(count)/float(len(municipality_ids)))*100
                    percent = "{0:.2f}".format(percent)
                    _logger.info('%s - %s%s (%s/%s)' % (
                        municipality_id.external_id,
                        percent,
                        '%',
                        count,
                        len(municipality_ids)
                    ))
                    # request
                    url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/%s/municipalities/' % self.external_id
                    payload = {
                        '$filter': '(name=='+str(municipality_id.name.encode('utf-8'))+')'
                    }                         
                    response = requests.get(url, params=payload)                    
                    if response.status_code == 200:
                        response_json = json.loads(response.text)
                        if 'provinces' in response_json:
                            for province in response_json['provinces']:
                                if 'municipalities' in province:
                                    for municipality in province['municipalities']:
                                        municipality_ids2 = self.env['property.municipality'].search(
                                            [
                                                ('property_state_id', '=', self.id),
                                                ('external_id', '=', str(municipality['id']))
                                            ]
                                        ) 
                                        if len(municipality_ids2) == 0:
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
                                            municipality_obj = self.env['property.municipality'].sudo().create(vals)
                                            # update
                                            municipality_id.property_municipality_id = municipality_obj.id
                        # Sleep 1 second to prevent error (if request)
                        time.sleep(1)                                                                        
                    else:
                        _logger.info('status_code')
                        _logger.info(response.status_code)                    
            # update date_last_check
            self.date_last_check = current_date.strftime("%Y-%m-%d")                                                
        # return
        return return_item    
    
    @api.model
    def cron_check_states(self):
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # all_items
        state_external_id = []
        state_ids = self.env['property.state'].search(
            [
                ('id', '>', 0)
            ]
        )
        if state_ids:
            for state_id in state_ids:
                state_external_id.append(str(state_id.external_id))
        # requests
        url = 'https://www.bbva.es/ASO/streetMap/V02/provinces'
        response = requests.get(url=url)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if 'provinces' in response_json:
                for province in response_json['provinces']:
                    if str(province['id']) not in state_external_id:
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
