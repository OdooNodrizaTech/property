# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models
import requests
import json
_logger = logging.getLogger(__name__)


class PropertyWayType(models.Model):
    _name = 'property.way.type'
    _description = 'Property way Type'

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
    def cron_check_way_types(self):
        # requests
        url = 'https://www.bbva.es/ASO/streetMap/V02/wayTypes/'
        response = requests.get(url=url)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if 'wayTypes' in response_json:
                if len(response_json['wayTypes']) > 0:
                    for way_type in response_json['wayTypes']:
                        if 'id' not in way_type:
                            continue

                        way_type_ids = self.env['property.way.type'].search(
                            [
                                ('source', '=', 'bbva'),
                                ('external_id', '=', str(way_type['id']))
                            ]
                        )
                        if len(way_type_ids) == 0:
                            # creamos
                            vals = {
                                'external_id': str(way_type['id']),
                                'name': str(way_type['name'].encode('utf-8')),
                                'source': 'bbva'
                            }
                            # create
                            self.env['property.way.type'].sudo().create(vals)
