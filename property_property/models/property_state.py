# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models
import requests
import json
from datetime import datetime
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
        string='Longitude'
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
        self.ensure_one()
        current_date = datetime.now()
        model_p_m = 'property.municipality'
        key_e_id = 'external_id'
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
                    url = 'https://%s/provinces/%s/municipalities/' % (
                        'www.bbva.es/ASO/streetMap/V02',
                        self.external_id
                    )
                    m_id_name = municipality_id.name
                    payload = {
                        '$filter': '(name=='+str(m_id_name.encode('utf-8'))+')'
                    }
                    response = requests.get(url, params=payload)
                    if response.status_code == 200:
                        response_json = json.loads(response.text)
                        if 'provinces' in response_json:
                            for province in response_json['provinces']:
                                if 'municipalities' in province:
                                    for municipality in province['municipalities']:
                                        municipality_ids2 = self.env[model_p_m].search(
                                            [
                                                ('property_state_id', '=', self.id),
                                                (key_e_id, '=', str(municipality['id']))
                                            ]
                                        )
                                        if len(municipality_ids2) == 0:
                                            # creamos
                                            m_name = municipality['name']
                                            vals = {
                                                'property_state_id': self.id,
                                                'external_id': str(municipality['id']),
                                                'name': str(m_name.encode('utf-8')),
                                                'source': 'bbva',
                                                'total_towns': 0
                                            }
                                            # location
                                            if 'location' in municipality:
                                                location = municipality['location']
                                                if 'value' in location:
                                                    value = location['value']
                                                    l_value = value.replace(',', '.')
                                                    l_value = l_value.split(';')
                                                    # _logger.info(location_value)
                                                    vals['latitude'] = str(l_value[1])
                                                    l0 = l_value[0]
                                                    l0 = l0.replace('-.', '-0.')
                                                    vals['longitude'] = str(l0)
                                            # create
                                            m_obj = self.env[
                                                model_p_m
                                            ].sudo().create(vals)
                                            # update
                                            m_id = municipality_id
                                            m_id.property_municipality_id = m_obj.id
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
                            location = province['location']
                            if 'value' in location:
                                value = location['value']
                                l_value = value.split(';')
                                vals['latitude'] = str(l_value[0])
                                vals['longitude'] = str(l_value[1])
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
