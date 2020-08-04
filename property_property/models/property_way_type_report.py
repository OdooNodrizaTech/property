# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models, _
import requests, xmltodict, json
from datetime import datetime
import pytz
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
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic %s' % self.env['ir.config_parameter'].sudo().get_param(
                'bbva_authorization_key'
            )
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
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # requests
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
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if 'levelDistribution' in response_json:
                if len(response_json['levelDistribution']) > 0:
                    for level_distribution_item in response_json['levelDistribution']:
                        if 'level' in level_distribution_item:
                            if 'id' in level_distribution_item['level']:
                                level_ids = self.env['property.level'].search(
                                    [
                                        ('external_id', '=', str(level_distribution_item['level']['id']))
                                    ]
                                )
                                if level_ids:
                                    level_id = level_ids[0]
                                    # vals
                                    vals = {
                                        'property_way_type_report_id': self.id,
                                        'property_level_id': level_id.id
                                    }
                                    # search
                                    report_detail_ids = self.env['property.way.type.report.detail'].search(
                                        [
                                            ('property_way_type_report_id', '=', self.id),
                                            ('property_level_id', '=', vals['property_level_id'])
                                        ]
                                    )
                                    if len(report_detail_ids) == 0:
                                        # name
                                        if 'name' in level_distribution_item:
                                            vals['name'] = str(level_distribution_item['name'])
                                        # flatDistribution
                                        if 'flatDistribution' in level_distribution_item:
                                            # freeOffer
                                            if 'freeOffer' in level_distribution_item['flatDistribution']:
                                                vals['flat_distribution_free_offer'] = level_distribution_item['flatDistribution']['freeOffer']
                                            # bankOffer
                                            if 'bankOffer' in level_distribution_item['flatDistribution']:
                                                vals['flat_distribution_bank_offer'] = level_distribution_item['flatDistribution']['bankOffer']
                                            # total
                                            if 'total' in level_distribution_item['flatDistribution']:
                                                vals['flat_distribution_total'] = level_distribution_item['flatDistribution']['total']
                                        # detachedPropertyDistribution
                                        if 'detachedPropertyDistribution' in level_distribution_item:
                                            # freeOffer
                                            if 'freeOffer' in level_distribution_item['detachedPropertyDistribution']:
                                                vals['detached_property_distribution_free_offer'] = level_distribution_item['detachedPropertyDistribution']['freeOffer']
                                            # bankOffer
                                            if 'bankOffer' in level_distribution_item['detachedPropertyDistribution']:
                                                vals['detached_property_distribution_bank_offer'] = level_distribution_item['detachedPropertyDistribution']['bankOffer']
                                            # total
                                            if 'total' in level_distribution_item['detachedPropertyDistribution']:
                                                vals['detached_property_distribution_total'] = level_distribution_item['detachedPropertyDistribution']['total']
                                        # create
                                        self.env['property.way.type.report.detail'].sudo().create(vals)
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
                        if return_item['errors'] == True:
                            _logger.info(return_item)
                            # fix
                            if return_item['status_code'] != 403:
                                _logger.info(paramos)
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
                        property_way_type_report_id.full = True
                    # Sleep 1 second to prevent error (if request)
                    time.sleep(1)
