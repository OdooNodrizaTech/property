# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models, _
import requests
import json
from datetime import datetime
import time
_logger = logging.getLogger(__name__)


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
            ('bbva', 'BBVA')
        ],
        string='Source',
        default='bbva'
    )

    @api.multi
    def bbva_generate_tsec(self):
        self.ensure_one()
        tsec = False
        url = 'https://www.bbva.es/ASO/TechArchitecture/grantingTicketsOauth/V01/'
        key = self.env['ir.config_parameter'].sudo().get_param('bbva_authorization_key')
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic %s' % key
        }
        data_obj = {
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, headers=headers, data=data_obj)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if 'access_token' in response_json:
                tsec = str(response_json['access_token'])

        return tsec

    @api.multi
    def action_check(self, tsec):
        self.ensure_one()
        current_date = datetime.now()
        model_p_w_a_r_d = 'property.way.area.report.detail'
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # requests
        url = 'https://%s/ASO/financialPropertyInformation/V01/%s/' % (
            'www.bbva.es',
            'getPropertyAreaReport'
        )
        body_obj = {
            "location": {
                "latitude": str(self.property_way_id.latitude),
                "longitude": str(self.property_way_id.longitude)
            },
            "radius": self.radius,
            "operationType": {
                "id": str(self.property_transaction_type_id.external_id)
            }
        }
        headers = {
            'content-type': 'application/json',
            'tsec': str(tsec)
        }
        _logger.info(self.property_way_id.id)
        response = requests.post(url, headers=headers, data=json.dumps(body_obj))
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if 'flatReport' in response_json:
                flatReport = response_json['flatReport']
                # total
                if 'total' in flatReport:
                    self.total = flatReport['total']
                # averageValue
                if 'averageValue' in flatReport:
                    if 'amount' in flatReport['averageValue']:
                        self.average_value = flatReport['averageValue']['amount']
                # averageSurfaceArea
                if 'averageSurfaceArea' in flatReport:
                    self.average_surface_area = flatReport['averageSurfaceArea']
                # percentage
                if 'percentage' in flatReport:
                    self.percentage = flatReport['percentage']
                # bedroomsReport
                if 'bedroomsReport' in flatReport:
                    bedroomsReport = flatReport['bedroomsReport']
                    if len(bedroomsReport) > 0:
                        for bedroom_item in bedroomsReport:
                            if 'bedroomsNumber' not in bedroom_item:
                                continue

                            # beedroom_number
                            beedroom_number = int(bedroom_item['bedroomsNumber'])
                            # search
                            ids = self.env[model_p_w_a_r_d].search(
                                [
                                    ('property_way_area_report_id', '=', self.id),
                                    ('beedroom_number', '=', beedroom_number)
                                ]
                            )
                            if len(ids) == 0:
                                # vals
                                vals = {
                                    'property_way_area_report_id': self.id,
                                    'beedroom_number': beedroom_number
                                }
                                # averageSurfaceArea
                                if 'averageSurfaceArea' in bedroom_item:
                                    vals[
                                        'average_surface'
                                    ] = bedroom_item['averageSurfaceArea']
                                # averagePrice
                                if 'averagePrice' in bedroom_item:
                                    averagePrice = bedroom_item['averagePrice']
                                    if 'amount' in averagePrice:
                                        vals['average_price'] = averagePrice['amount']
                                # percentage
                                if 'percentage' in bedroom_item:
                                    vals['percentage'] = bedroom_item['percentage']
                                # create
                                self.env[model_p_w_a_r_d].sudo().create(vals)
        # update date_last_check + total_build_units
        self.date_last_check = current_date.strftime("%Y-%m-%d")
        # return
        return return_item

    @api.model
    def cron_check_ways_area_report(self):
        transaction_type_ids = self.env['property.transaction.type'].search(
            [
                ('id', '>', 0)
            ]
        )
        if transaction_type_ids:
            for transaction_type_id in transaction_type_ids:
                area_report_ids = self.env['property.way.area.report'].search(
                    [
                        ('property_transaction_type_id', '=', transaction_type_id.id)
                    ]
                )
                if area_report_ids:
                    way_ids = self.env['property.way'].search(
                        [
                            (
                                'id',
                                'not in',
                                area_report_ids.mapped('property_way_id').ids
                            ),
                            ('latitude', '!=', False),
                            ('longitude', '!=', False)
                        ]
                    )
                else:
                    way_ids = self.env['property.way'].search(
                        [
                            ('latitude', '!=', False),
                            ('longitude', '!=', False)
                        ]
                    )
                # operations-generate
                if way_ids:
                    for way_id in way_ids:
                        # cals
                        vals = {
                            'property_way_id': way_id.id,
                            'property_transaction_type_id': transaction_type_id.id,
                            'radius': 1000,
                            'source': 'bbva'
                        }
                        self.env['property.way.area.report'].sudo().create(vals)
        # now check all property.way.area.report
        area_report_ids = self.env['property.way.area.report'].search(
            [
                ('full', '=', False)
            ],
            limit=2000
        )
        if area_report_ids:
            count = 0
            # generate_tsec
            tsec = self.bbva_generate_tsec()
            if tsec:
                for area_report_id in area_report_ids:
                    count += 1
                    # action_check
                    return_item = area_report_id.action_check(tsec)[0]
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
                                tsec = self.bbva_generate_tsec()
                    # _logger
                    percent = (float(count)/float(len(area_report_ids)))*100
                    percent = "{0:.2f}".format(percent)
                    _logger.info('%s - %s%s (%s/%s)' % (
                        area_report_id.id,
                        percent,
                        '%',
                        count,
                        len(area_report_ids)
                    ))
                    # update
                    if return_item['status_code'] != 403:
                        area_report_id.full = True
                    # Sleep 1 second to prevent error (if request)
                    time.sleep(1)
