# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models, _
import requests
import json
from datetime import datetime
import time
_logger = logging.getLogger(__name__)


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
        string='Longitude'
    )
    full = fields.Boolean(
        string='Full'
    )
    date_last_check = fields.Date(
        string='Date Last Check'
    )
    source = fields.Selection(
        selection=[
            ('bbva', 'BBVA')
        ],
        string='Source',
        default='bbva'
    )
    total_numbers = fields.Integer(
        string='Total Numbers'
    )

    @api.multi
    def action_update_way(self):
        self.ensure_one()
        current_date = datetime.now()
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # distritopostal.way
        way_ids = self.env['distritopostal.way'].search(
            [
                ('property_way_id', '=', self.id)
            ]
        )
        if way_ids:
            way_id = way_ids[0]
            # request
            url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/%s/municipalities/%s/towns/%s/ways' % (
                self.property_town_id.property_municipality_id.property_state_id.external_id,
                self.property_town_id.property_municipality_id.external_id,
                self.property_town_id.external_id
            )
            payload = {
                '$filter': '(name=='+str(way_id.name.encode('utf-8'))+')'
            }
            response = requests.get(url, params=payload)
            if response.status_code == 200:
                response_json = json.loads(response.text)
                if 'provinces' in response_json:
                    for province in response_json['provinces']:
                        if 'municipalities' in province:
                            for municipality in province['municipalities']:
                                if 'towns' in municipality:
                                    for town in municipality['towns']:
                                        if 'ways' in town:
                                            for way in town['ways']:
                                                # latitude-longitude
                                                if 'location' in way:
                                                    location_value = way['location']['value'].replace(',', '.').split(';')
                                                    self.latitude = str(location_value[1])
                                                    # longitude
                                                    self.longitude = str(location_value[0].replace('-.', '-0.'))
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
    def action_get_numbers(self):
        self.ensure_one()
        current_date = datetime.now()
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # requests
        total_numbers = 0
        url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/%s/municipalities/%s/ways/%s/numbers' % (
            self.property_town_id.property_municipality_id.property_state_id.external_id,
            self.property_town_id.property_municipality_id.external_id,
            self.external_id
        )
        response = requests.get(url)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            # operations
            if 'provinces' in response_json:
                for province in response_json['provinces']:
                    if province['id'] == self.property_town_id.property_municipality_id.property_state_id.external_id:
                        if 'municipalities' in province:
                            for municipality in province['municipalities']:
                                if 'towns' in municipality:
                                    for town in municipality['towns']:
                                        if 'ways' in town:
                                            for way in town['ways']:
                                                if str(way['id']) == self.external_id:
                                                    if 'numbers' in way:
                                                        for number in way['numbers']:
                                                            number_ids = self.env['property.number'].search(
                                                                [
                                                                    ('property_way_id', '=', self.id),
                                                                    ('external_id', '=', str(number['id']))
                                                                ]
                                                            )
                                                            if len(number_ids) == 0:
                                                                # creamos
                                                                vals = {
                                                                    'property_way_id': self.id,
                                                                    'external_id': str(number['id']),
                                                                    'source': 'bbva'
                                                                }
                                                                # latitude-longitude
                                                                if 'name' in number:
                                                                    vals['name'] = str(number['name'].encode('utf-8'))
                                                                # create
                                                                self.env['property.number'].sudo().create(vals)
                                                                # total_numbers
                                                                total_numbers += 1
        else:
            _logger.info('status_code')
            _logger.info(response.status_code)
            _logger.info(url)
        # update date_last_check + total_numbers
        self.date_last_check = current_date.strftime("%Y-%m-%d")
        self.total_numbers = total_numbers
        # return
        return return_item

    @api.model
    def cron_check_ways(self):
        municipality_ids = self.env['property.municipality'].search(
            [
                ('full_ways', '=', False)
            ]
        )
        if municipality_ids:
            count = 0
            for municipality_id in municipality_ids:
                count += 1
                # action_get_ways
                return_item = municipality_id.action_get_ways()[0]
                if 'errors' in return_item:
                    if return_item['errors']:
                        _logger.info(return_item)
                        # fix
                        if return_item['status_code'] != 403:
                            break
                        else:
                            _logger.info(
                                _('Raro que sea un 403 pero pasamos')
                            )
                # _logger
                percent = (float(count)/float(len(municipality_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s - %s%s (%s/%s)' % (
                    municipality_id.name.encode('utf-8'),
                    percent,
                    '%',
                    count,
                    len(municipality_ids)
                ))
                # update
                municipality_id.full_ways = True

    @api.model
    def cron_update_ways(self):
        way_ids = self.env['property.way'].search(
            [
                ('full', '=', True)
            ]
        )
        if way_ids:
            count = 0
            for way_id in way_ids:
                count += 1
                # action_get_municipalities
                return_item = way_id.action_update_way()[0]
                if 'errors' in return_item:
                    if return_item['errors']:
                        _logger.info(return_item)
                        # fix
                        if return_item['status_code'] != 403:
                            break
                        else:
                            _logger.info(
                                _('Raro que sea un 403 pero pasamos')
                            )
                # _logger
                percent = (float(count)/float(len(way_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s - %s%s (%s/%s)' % (
                    way_id.id,
                    percent,
                    '%',
                    count,
                    len(way_ids)
                ))
