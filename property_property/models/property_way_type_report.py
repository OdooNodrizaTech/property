# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models, _
import requests
import json
from datetime import datetime
import time
_logger = logging.getLogger(__name__)


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
        model_p_w_t_r_d = 'property.way.type.report.detail'
        key_e_id = 'external_id'
        key_p_w_t_r_id = 'property_way_type_report_id'
        key_p_l_id = 'property_level_id'
        key_d_p_d_f_o = 'detached_property_distribution_free_offer'
        key_d_p_d_b_o = 'detached_property_distribution_bank_offer'
        key_d_p_d_t = 'detached_property_distribution_total'
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # requests
        url = 'https://%s/ASO/financialPropertyInformation/V01/%s/' % (
            'www.bbva.es',
            'getPropertyTypeReport'
        )
        body_obj = {
            "location": {
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
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if 'levelDistribution' in response_json:
                if len(response_json['levelDistribution']) > 0:
                    for ld_item in response_json['levelDistribution']:
                        if 'level' not in ld_item:
                            continue

                        if 'id' not in ld_item['level']:
                            continue

                        level_ids = self.env['property.level'].search(
                            [
                                (key_e_id, '=', str(ld_item['level']['id']))
                            ]
                        )
                        if level_ids:
                            level_id = level_ids[0]
                            # vals
                            vals = {
                                key_p_w_t_r_id: self.id,
                                key_p_l_id: level_id.id
                            }
                            # search
                            detail_ids = self.env[model_p_w_t_r_d].search(
                                [
                                    (key_p_w_t_r_id, '=', self.id),
                                    (key_p_l_id, '=', vals['property_level_id'])
                                ]
                            )
                            if len(detail_ids) == 0:
                                # name
                                if 'name' in ld_item:
                                    vals['name'] = str(ld_item['name'])
                                # flatDistribution
                                if 'flatDistribution' in ld_item:
                                    flatDistribution = ld_item['flatDistribution']
                                    # freeOffer
                                    if 'freeOffer' in flatDistribution:
                                        vals[
                                            'flat_distribution_free_offer'
                                        ] = flatDistribution['freeOffer']
                                    # bankOffer
                                    if 'bankOffer' in flatDistribution:
                                        vals[
                                            'flat_distribution_bank_offer'
                                        ] = flatDistribution['bankOffer']
                                    # total
                                    if 'total' in flatDistribution:
                                        vals[
                                            'flat_distribution_total'
                                        ] = flatDistribution['total']
                                # detachedPropertyDistribution
                                if 'detachedPropertyDistribution' in ld_item:
                                    d_p_d = ld_item['detachedPropertyDistribution']
                                    # freeOffer
                                    if 'freeOffer' in d_p_d:
                                        vals[key_d_p_d_f_o] = d_p_d['freeOffer']
                                    # bankOffer
                                    if 'bankOffer' in d_p_d:
                                        vals[key_d_p_d_b_o] = d_p_d['bankOffer']
                                    # total
                                    if 'total' in d_p_d:
                                        vals[key_d_p_d_t] = d_p_d['total']
                                # create
                                self.env[model_p_w_t_r_d].sudo().create(vals)
        # update date_last_check + total_build_units
        self.date_last_check = current_date.strftime("%Y-%m-%d")
        # return
        return return_item

    @api.model
    def cron_check_ways_type_report(self):
        type_report_ids = self.env['property.way.type.report'].search(
            [
                ('id', '>', 0)
            ]
        )
        if type_report_ids:
            way_ids = self.env['property.way'].search(
                [
                    ('id', 'not in', type_report_ids.mapped('property_way_id').ids),
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
                # vals
                vals = {
                    'property_way_id': way_id.id,
                    'source': 'bbva'
                }
                self.env['property.way.type.report'].sudo().create(vals)
        # now check all property.way.type.report
        type_report_ids = self.env['property.way.type.report'].search(
            [
                ('full', '=', False)
            ],
            limit=2000
        )
        if type_report_ids:
            count = 0
            # generate_tsec
            tsec = self.bbva_generate_tsec()
            if tsec:
                for type_report_id in type_report_ids:
                    count += 1
                    # action_check
                    return_item = type_report_id.action_check(tsec)[0]
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
                    percent = (float(count)/float(len(type_report_ids)))*100
                    percent = "{0:.2f}".format(percent)
                    _logger.info('%s - %s%s (%s/%s)' % (
                        type_report_id.id,
                        percent,
                        '%',
                        count,
                        len(type_report_ids)
                    ))
                    # update
                    if return_item['status_code'] != 403:
                        type_report_id.full = True
                    # Sleep 1 second to prevent error (if request)
                    time.sleep(1)
