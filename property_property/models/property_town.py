# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

class PropertyWay(models.Model):
    _name = 'property.town'
    _description = 'Property town'
    
    property_municipality_id = fields.Many2one(
        comodel_name='property.municipality',
        string='Property Municipality Id'
    )
    external_id = fields.Char(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
    )        
    source = fields.Selection(
        selection=[
            ('bbva','BBVA')                                      
        ],
        string='Source',
        default='bbva'
    )            
    
    @api.multi    
    def cron_check_towns(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_towns')
        
        property_municipality_ids = self.env['property.municipality'].search([('full', '=', False)])
        if property_municipality_ids:
            count = 0
            for property_municipality_id in property_municipality_ids:
                count += 1
                # action_get_towns
                return_item = property_municipality_id.action_get_towns()[0]
                if 'errors' in return_item:
                    if return_item['errors'] == True:
                        _logger.info(return_item)
                        # fix
                        if return_item['status_code'] != 403:
                            _logger.info(paramos)
                        else:
                            _logger.info('Raro que sea un 403 pero pasamos')
                # _logger
                percent = (float(count)/float(len(property_municipality_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s - %s%s (%s/%s)' % (
                    property_municipality_id.name.encode('utf-8'),
                    percent,
                    '%',
                    count,
                    len(property_municipality_ids)
                ))
                # update
                property_municipality_id.full = True
                # Sleep 1 second to prevent error (if request)
                time.sleep(1)    