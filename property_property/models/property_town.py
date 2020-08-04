# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models, _
import requests, xmltodict, json
from datetime import datetime
import pytz
import time
_logger = logging.getLogger(__name__)


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
            ('bbva', 'BBVA')
        ],
        string='Source',
        default='bbva'
    )

    @api.model
    def cron_check_towns(self):
        municipality_ids = self.env['property.municipality'].search(
            [
                ('full', '=', False)
            ]
        )
        if municipality_ids:
            count = 0
            for municipality_id in municipality_ids:
                count += 1
                # action_get_towns
                return_item = municipality_id.action_get_towns()[0]
                if 'errors' in return_item:
                    if return_item['errors']:
                        _logger.info(return_item)
                        # fix
                        if return_item['status_code'] != 403:
                            _logger.info(paramos)
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
                municipality_id.full = True
                # Sleep 1 second to prevent error (if request)
                time.sleep(1)
