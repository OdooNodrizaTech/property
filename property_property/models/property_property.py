# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models, _
import requests
import json
from datetime import datetime
import time
_logger = logging.getLogger(__name__)


class PropertyProperty(models.Model):
    _name = 'property.property'
    _description = 'Property Property'

    property_number_id = fields.Many2one(
        comodel_name='property.number',
        string='Property Number Id'
    )
    external_id = fields.Char(
        string='External Id'
    )
    surface_area = fields.Integer(
        string='Surface Area'
    )
    plot_surface_area = fields.Integer(
        string='Plot Surface Area'
    )
    built_surface_area = fields.Integer(
        string='Built Surface Area'
    )
    coefficient = fields.Float(
        string='Coefficient'
    )
    property_use_id = fields.Many2one(
        comodel_name='property.use',
        string='Property Use Id'
    )
    property_building_type_id = fields.Many2one(
        comodel_name='property.building.type',
        string='Property Building Type Id'
    )
    year_old = fields.Integer(
        string='Year Old'
    )
    building_year = fields.Integer(
        string='Building Year'
    )
    reform_year = fields.Integer(
        string='Reform Year'
    )
    plot_registry_id = fields.Char(
        string='Plot Registry Id'
    )
    stair = fields.Char(
        string='Stair'
    )
    floor = fields.Char(
        string='Floor'
    )
    door = fields.Char(
        string='Door'
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
    total_build_units = fields.Integer(
        string='Total Build Units'
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
    def action_get_full_info(self, tsec, use_id_external_id=False):
        self.ensure_one()
        current_date = datetime.now()
        p_town_id = self.property_number_id.property_way_id.property_town_id
        model_p_o_b_u = 'property.property.build.unit'
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # property_use_id_external_id
        if not use_id_external_id:
            use_id_external_id = []
            use_ids = self.env['property.use'].search(
                [
                    ('id', '>', 0)
                ]
            )
            if use_ids:
                for use_id in use_ids:
                    use_id_external_id[str(use_id.external_id)] = use_id.id
        # requests
        total_build_units = 0
        url = '%s%s/municipalities/%s/towns/%s/ways/%s/numbers/%s/properties/%s' % (
            'https://www.bbva.es/ASO/streetMap/V02/provinces',
            p_town_id.property_municipality_id.property_state_id.external_id,
            p_town_id.property_municipality_id.external_id,
            p_town_id.external_id,
            self.property_number_id.property_way_id.external_id,
            self.property_number_id.external_id,
            self.external_id
        )
        headers = {'tsec': str(tsec)}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            for province in response_json['provinces']:
                if 'municipalities' not in province:
                    continue

                for municipality in province['municipalities']:
                    if 'towns' not in municipality:
                        continue

                    for town in municipality['towns']:
                        if 'ways' not in town:
                            continue

                        for way in town['ways']:
                            if 'numbers' not in way:
                                continue

                            for number in way['numbers']:
                                if 'properties' not in number:
                                    continue

                                for property in number['properties']:
                                    # stair
                                    if 'stair' in property:
                                        self.stair = str(property['stair'])
                                    # floor
                                    if 'floor' in property:
                                        self.floor = str(property['floor'])
                                    # door
                                    if 'door' in property:
                                        self.door = str(property['door'])
                                    # buildUnits
                                    if 'buildUnits' not in property:
                                        continue

                                    for bu in property['buildUnits']:
                                        if 'id' not in bu:
                                            continue

                                        build_unit_ids = self.env[model_p_o_b_u].search(
                                            [
                                                ('property_property_id', '=', self.id),
                                                ('external_id', '=', str(bu['id']))
                                            ]
                                        )
                                        if build_unit_ids:
                                            # vals
                                            vals = {
                                                'property_property_id': self.id,
                                                'external_id': str(bu['id']),
                                                'source': 'bbva'
                                            }
                                            # stair
                                            if 'stair' in bu:
                                                vals['stair'] = str(bu['stair'])
                                            # floor
                                            if 'floor'in build_unit:
                                                vals['floor'] = str(bu['floor'])
                                            # door
                                            if 'door' in build_unit:
                                                vals['door'] = str(bu['door'])
                                            # builtSurfaceArea
                                            if 'builtSurfaceArea' in bu:
                                                vals[
                                                    'built_surface_area'
                                                ] = int(bu['builtSurfaceArea'])
                                            # useCode
                                            if 'useCode' in bu:
                                                if 'id' in bu['useCode']:
                                                    uC_id = str(bu['useCode'])
                                                    if uC_id in use_id_external_id:
                                                        val = use_id_external_id[uC_id]
                                                        vals['property_use_id'] = val
                                            # create
                                            self.env[model_p_o_b_u].sudo().create(vals)
                                            # total_build_units
                                            total_build_units += 1
        else:
            _logger.info('status_code')
            _logger.info(response.status_code)
            _logger.info(url)
        # update date_last_check + total_build_units
        self.date_last_check = current_date.strftime("%Y-%m-%d")
        self.total_build_units = total_build_units
        # return
        return return_item

    @api.model
    def cron_check_properties(self):
        self.ensure_one()
        number_ids = self.env['property.number'].search(
            [
                ('full', '=', False)
            ],
            limit=3000
        )
        if number_ids:
            count = 0
            # generate_tsec
            tsec = self.bbva_generate_tsec()
            if tsec:
                # use_id_external_id (optimize multi-query)
                use_id_external_id = {}
                use_ids = self.env['property.use'].search(
                    [
                        ('id', '>', 0)
                    ]
                )
                if use_ids:
                    for use_id in use_ids:
                        use_id_external_id[str(use_id.external_id)] = use_id.id
                # building_type_id_external_id (optimize multi-query)
                type_id_external_id = {}
                building_type_ids = self.env['property.building.type'].search(
                    [
                        ('id', '>', 0)
                    ]
                )
                if building_type_ids:
                    for type_id in building_type_ids:
                        type_id_external_id[str(type_id.external_id)] = type_id.id
                # for
                for number_id in number_ids:
                    count += 1
                    # action_get_properties
                    return_item = number_id.action_get_properties(
                        tsec,
                        use_id_external_id,
                        type_id_external_id
                    )[0]
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
                                # generamos de nuevo el tsecs
                                tsec = self.bbva_generate_tsec()
                    # _logger
                    percent = (float(count)/float(len(number_ids)))*100
                    percent = "{0:.2f}".format(percent)
                    _logger.info('%s - %s%s (%s/%s)' % (
                        number_id.id,
                        percent,
                        '%',
                        count,
                        len(number_ids)
                    ))
                    # update
                    if return_item['status_code'] != 403:
                        number_id.full = True
                    # Sleep 1 second to prevent error (if request)
                    time.sleep(1)

    @api.model
    def cron_check_properties_full_info(self):
        property_ids = self.env['property.property'].search(
            [
                ('full', '=', False)
            ],
            limit=3000
        )
        if property_ids:
            # generate_tsec
            tsec = self.bbva_generate_tsec()
            if tsec:
                count = 0
                # use_id_external_id (optimize multi-query)
                use_id_external_id = {}
                use_ids = self.env['property.use'].search(
                    [
                        ('id', '>', 0)
                    ]
                )
                if use_ids:
                    for use_id in use_ids:
                        use_id_external_id[str(use_id.external_id)] = use_id.id
                # for
                for property_id in property_ids:
                    count += 1
                    # action_get_full_info
                    return_item = property_id.action_get_full_info(
                        tsec,
                        use_id_external_id
                    )[0]
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
                                # generamos de nuevo el tsecs
                                tsec = self.bbva_generate_tsec()
                    # _logger
                    percent = (float(count)/float(len(property_ids)))*100
                    percent = "{0:.2f}".format(percent)
                    _logger.info('%s - %s%s (%s/%s)' % (
                        property_id.external_id,
                        percent,
                        '%',
                        count,
                        len(property_ids)
                    ))
                    # update
                    if return_item['status_code'] == 200:
                        property_id.full = True
                    # Sleep 1 second to prevent error (if request)
                    time.sleep(1)
