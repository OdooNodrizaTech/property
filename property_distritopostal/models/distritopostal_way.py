# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models
_logger = logging.getLogger(__name__)


class DistritopostalWay(models.Model):
    _name = 'distritopostal.way'
    _description = 'Distritopostal Way'
    
    distritopostal_municipality_id = fields.Many2one(
        comodel_name='distritopostal.municipality',
        string='Distritopostal Municipality Id'
    )
    distritopostal_postalcode_id = fields.Many2one(
        comodel_name='distritopostal.postalcode',
        string='Distritopostal Postalcode Id'
    )    
    name = fields.Char(
        string='Name'
    )
    
    @api.model    
    def cron_check_ways_distritopostal(self):
        _logger.info('cron_check_ways_distritopostal')
        # postalcode
        postalcode_ids = self.env['distritopostal.postalcode'].search(
            [
                ('full', '=', False)
            ],
            limit=1000
        )
        if postalcode_ids:
            count = 0
            for postalcode_id in postalcode_ids:
                count += 1
                # action_get_ways
                postalcode_id.action_get_ways()[0]
                # _logger
                percent = (float(count)/float(len(postalcode_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s- %s %s (%s/%s)' % (
                    postalcode_id.url,
                    percent,
                    '%',
                    count,
                    len(postalcode_ids)
                ))
        # municipality
        municipality_ids = self.env['distritopostal.municipality'].search(
            [
                ('full', '=', False)
            ],
            limit=1000
        )
        _logger.info(len(municipality_ids))
        if municipality_ids:
            count = 0
            for municipality_id in municipality_ids:
                count += 1
                # action_get_ways
                municipality_id.action_get_ways()[0]
                # _logger
                percent = (float(count)/float(len(municipality_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s- %s %s (%s/%s)' % (
                    municipality_id.url,
                    percent,
                    '%',
                    count,
                    len(municipality_ids)
                ))
