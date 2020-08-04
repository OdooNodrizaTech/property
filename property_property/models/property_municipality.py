# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models, _
import requests
import json
from datetime import datetime
import time
_logger = logging.getLogger(__name__)


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
            ('bbva', 'BBVA')
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

    @api.multi
    def action_update_municipality(self):
        self.ensure_one()
        current_date = datetime.now()
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # distritopostal.municipality
        municipality_ids = self.env['distritopostal.municipality'].search(
            [
                ('property_municipality_id', '=', self.id)
            ]
        )
        if municipality_ids:
            municipality_id = municipality_ids[0]
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
                                if 'location' in municipality:
                                    if 'value' in municipality['location']:
                                        location_value = municipality['location']['value'].replace(',', '.').split(';')
                                        self.latitude = str(location_value[1])
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
    def action_get_towns(self):
        self.ensure_one()
        current_date = datetime.now()
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # operations
        total_towns = 0
        url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/%s/municipalities/%s/towns' % (
            self.property_state_id.external_id,
            self.external_id
        )
        response = requests.get(url)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if 'provinces' in response_json:
                for province in response_json['provinces']:
                    if 'municipalities' in province:
                        for municipality in province['municipalities']:
                            if 'towns' in municipality:
                                for town in municipality['towns']:
                                    town_ids = self.env['property.town'].search(
                                        [
                                            ('property_municipality_id', '=', self.id),
                                            ('external_id', '=', str(town['id']))
                                        ]
                                    )
                                    if len(town_ids) == 0:
                                        # creamos
                                        vals = {
                                            'property_municipality_id': self.id,
                                            'external_id': str(town['id']),
                                            'name': str(town['name'].encode('utf-8')),
                                            'source': 'bbva'
                                        }
                                        self.env['property.town'].sudo().create(vals)
                                        # total_towns
                                        total_towns += 1
        else:
            _logger.info('status_code')
            _logger.info(response.status_code)
        # update date_last_check
        self.date_last_check = current_date.strftime("%Y-%m-%d")
        self.total_towns = total_towns
        # return
        return return_item

    @api.model
    def cron_check_municipalities(self):
        state_ids = self.env['property.state'].search(
            [
                ('full', '=', False)
            ]
        )
        if state_ids:
            count = 0
            for state_id in state_ids:
                count += 1
                # action_get_municipalities
                return_item = state_id.action_get_municipalities()[0]
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
                percent = (float(count)/float(len(state_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s - %s%s (%s/%s)' % (
                    state_id.id,
                    percent,
                    '%',
                    count,
                    len(state_ids)
                ))
                # update
                state_id.full = True
                # Sleep 1 second to prevent error (if request)
                time.sleep(1)

    @api.model
    def cron_update_municipalities(self):
        municipality_ids = self.env['property.municipality'].search(
            [
                ('full', '=', True)
            ]
        )
        if municipality_ids:
            count = 0
            for municipality_id in municipality_ids:
                count += 1
                # action_update_municipality
                return_item = municipality_id.action_update_municipality()[0]
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
                    municipality_id.id,
                    percent,
                    '%',
                    count,
                    len(municipality_ids)
                ))

    @api.multi
    def action_get_ways(self):
        self.ensure_one()
        current_date = datetime.now()
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        total_ways = 0
        # distritopostal.municipality
        municipality_ids = self.env['distritopostal.municipality'].search(
            [
                ('property_municipality_id', '=', self.id)
            ]
        )
        if municipality_ids:
            municipality_id = municipality_ids[0]
            way_ids = self.env['distritopostal.way'].search(
                [
                    ('distritopostal_municipality_id', '=', municipality_id.id)
                ]
            )
            if way_ids:
                count = 0
                for way_id in way_ids:
                    count += 1
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
                    # request
                    url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/%s/municipalities/%s/ways' % (
                        self.property_state_id.external_id,
                        self.external_id
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
                                                if 'id' in town:
                                                    town_ids = self.env['property.town'].search(
                                                        [
                                                            ('property_municipality_id', '=', self.id),
                                                            ('external_id', '=', str(town['id']))
                                                        ]
                                                    )
                                                    if town_ids:
                                                        town_id = town_ids[0]
                                                        # ways
                                                        if 'ways' in town:
                                                            for way in town['ways']:
                                                                way_ids2 = self.env['property.way'].search(
                                                                    [
                                                                        ('property_town_id', '=', self.id),
                                                                        ('external_id', '=', str(way['id']))
                                                                    ]
                                                                )
                                                                if len(way_ids2) == 0:
                                                                    # creamos
                                                                    vals = {
                                                                        'property_town_id': town_id.id,
                                                                        'external_id': str(way['id']),
                                                                        'name': str(way['name'].encode('utf-8')),
                                                                        'source': 'bbva'
                                                                    }
                                                                    # postalCode
                                                                    if 'postalCode' in way:
                                                                        vals['postal_code'] = str(way['postalCode'])
                                                                    # type
                                                                    if 'type' in way:
                                                                        if 'id' in way['type']:
                                                                            way_type_ids = self.env['property.way.type'].search(
                                                                                [
                                                                                    ('source', '=', 'bbva'),
                                                                                    ('external_id', '=', str(way['type']['id']))
                                                                                ]
                                                                            )
                                                                            if way_type_ids:
                                                                                vals['property_way_type_id'] = way_type_ids[0].id
                                                                    # latitude-longitude
                                                                    if 'location' in way:
                                                                        location_value = way['location']['value'].replace(',', '.').split(';')
                                                                        vals['latitude'] = str(location_value[1])
                                                                        vals['longitude'] = str(location_value[0].replace('-.', '-0.'))
                                                                    # create
                                                                    way_obj = self.env['property.way'].sudo().create(vals)
                                                                    # distritopostal_way_id
                                                                    way_id.property_way_id = way_obj.id
                                                                    # total_ways
                                                                    total_ways += 1
                        # Sleep 1 second to prevent error (if request)
                        time.sleep(1)
                    else:
                        _logger.info('status_code')
                        _logger.info(response.status_code)
            # update date_last_check
            self.date_last_check = current_date.strftime("%Y-%m-%d")
            self.total_ways = total_ways
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
                town_ids = self.env['property.town'].search(
                    [
                        ('property_municipality_id', '=', municipality_id.id)
                    ]
                )
                if town_ids:  # suponemos que si tiene 1 o + ya estan importados
                    count += 1
                    # action_get_municipalities
                    return_item = municipality_id.action_get_ways()[0]
                    if 'errors' in return_item:
                        if return_item['errors']:
                            _logger.info(return_item)
                            # fix
                            if return_item['status_code'] != 403:
                                break
                            else:
                                _logger.info('Raro que sea un 403 pero pasamos')
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
