# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models, _
import requests
import json
from datetime import datetime
import time
_logger = logging.getLogger(__name__)


class PropertyNumber(models.Model):
    _name = 'property.number'
    _description = 'Property Number'

    property_way_id = fields.Many2one(
        comodel_name='property.way',
        string='Property Way Id'
    )
    external_id = fields.Char(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
    )
    inhabitants_house_hold_ratio = fields.Integer(
        string='Inhabitants House Hold Ratio'
    )
    house_holds_number = fields.Integer(
        string='House Holds Number'
    )
    floors_number = fields.Integer(
        string='Floors Number'
    )
    profesional_activities_number = fields.Integer(
        string='Profesional Activities Number'
    )
    companies_number = fields.Integer(
        string='Companies Number'
    )
    office_numbers = fields.Integer(
        string='Office Numbers'
    )
    commercials_number = fields.Integer(
        string='Commercials Number'
    )
    garages_number = fields.Integer(
        string='Garages Number'
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
    total_properties = fields.Integer(
        string='Total Properties'
    )

    @api.multi
    def action_get_properties(self,
                              tsec,
                              use_id_external_id=False,
                              bt_id_external_id=False
                              ):
        self.ensure_one()
        current_date = datetime.now()
        p_m_id = self.property_way_id.property_town_id.property_municipality_id
        model_p_p = 'property.property'
        model_p_b_t = 'property.building.type'
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # property_use_id_external_id
        if not use_id_external_id:
            use_id_external_id = {}
            use_ids = self.env['property.use'].search(
                [
                    ('id', '>', 0)
                ]
            )
            if use_ids:
                for use_id in use_ids:
                    use_id_external_id[str(use_id.external_id)] = use_id.id
        # property_building_type_id_external_id
        if not bt_id_external_id:
            bt_id_external_id = {}
            building_type_ids = self.env['property.building.type'].search(
                [
                    ('id', '>', 0)
                ]
            )
            if building_type_ids:
                for type_id in building_type_ids:
                    bt_id_external_id[str(type_id.external_id)] = type_id.id
        # requests
        total_properties = 0
        url = '%s/%s/municipalities/%s/towns/%s/ways/%s/numbers/%s/' % (
            'https://www.bbva.es/ASO/streetMap/V02/provinces',
            p_m_id.property_state_id.external_id,
            p_m_id.external_id,
            self.property_way_id.property_town_id.external_id,
            self.property_way_id.external_id,
            self.external_id
        )
        headers = {
            'tsec': str(tsec)
        }
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
                                # update_number_info
                                # inhabitantsHouseHoldRatio
                                if 'inhabitantsHouseHoldRatio' in number:
                                    self.inhabitants_house_hold_ratio = number[
                                        'inhabitantsHouseHoldRatio'
                                    ]
                                # houseHoldsNumber
                                if 'houseHoldsNumber' in number:
                                    self.house_holds_number = number['houseHoldsNumber']
                                # floorsNumber
                                if 'floorsNumber' in number:
                                    self.floors_number = number['floorsNumber']
                                # profesionalActivitiesNumber
                                if 'profesionalActivitiesNumber' in number:
                                    self.profesional_activities_number = number[
                                        'profesionalActivitiesNumber'
                                    ]
                                # companiesNumber
                                if 'companiesNumber' in number:
                                    self.companies_number = number['companiesNumber']
                                # officeNumbers
                                if 'officeNumbers' in number:
                                    self.office_numbers = number['officeNumbers']
                                # commercialsNumber
                                if 'commercialsNumber' in number:
                                    self.commercials_number = number[
                                        'commercialsNumber'
                                    ]
                                # garagesNumber
                                if 'garagesNumber' in number:
                                    self.garages_number = number['garagesNumber']
                                # properties
                                if 'properties' in number:
                                    for property in number['properties']:
                                        property_id = str(property['id'])
                                        property_ids = self.env[model_p_p].search(
                                            [
                                                ('property_number_id', '=', self.id),
                                                ('external_id', '=', property_id)
                                            ]
                                        )
                                        if len(property_ids) == 0:
                                            # creamos
                                            vals = {
                                                'property_number_id': self.id,
                                                'external_id': str(property['id']),
                                                'source': 'bbva',
                                                'total_build_units': 0
                                            }
                                            # surfaceArea
                                            if 'surfaceArea' in property:
                                                surfaceArea = property['surfaceArea']
                                                vals['surface_area'] = str(surfaceArea)
                                            # plotSurfaceArea
                                            if 'plotSurfaceArea' in property:
                                                vals[
                                                    'plot_surface_area'
                                                ] = int(property['plotSurfaceArea'])
                                            # builtSurfaceArea
                                            if 'builtSurfaceArea' in property:
                                                vals[
                                                    'built_surface_area'
                                                ] = int(property['builtSurfaceArea'])
                                            # coefficient
                                            if 'coefficient' in property:
                                                coefficient = property['coefficient']
                                                vals[
                                                    'coefficient'
                                                ] = str(coefficient.replace(',', '.'))
                                            # yearOld
                                            if 'yearOld' in property:
                                                yearOld = property['yearOld']
                                                vals['year_old'] = int(yearOld)
                                            # buildingYear
                                            if 'buildingYear' in property:
                                                vals[
                                                    'building_year'
                                                ] = int(property['buildingYear'])
                                            # reformYear
                                            if 'reformYear' in property:
                                                vals[
                                                    'reform_year'
                                                ] = int(property['reformYear'])
                                            # plotRegistryId
                                            if 'plotRegistryId' in property:
                                                vals[
                                                    'plot_registry_id'
                                                ] = str(property['plotRegistryId'])
                                            # property_user_id
                                            if 'useCode' in property:
                                                useCode = property['useCode']
                                                if 'id' in useCode:
                                                    uCid = str(useCode['id'])
                                                    uCname = property['useCode']['name']
                                                    UCname = uCname.encode('utf-8')
                                                    # if not exists create
                                                    if uCid not in use_id_external_id:
                                                        use_vals = {
                                                            'external_id': uCid,
                                                            'name': UCname,
                                                        }
                                                        use_obj = self.env[
                                                            'property.use'
                                                        ].sudo().create(use_vals)
                                                        # add_array
                                                        e_id = use_vals['external_id']
                                                        use_id_external_id[
                                                            str(e_id)
                                                        ] = use_obj.id
                                                    # check_if_exists and add
                                                    if uCid in use_id_external_id:
                                                        vals[
                                                            'property_user_id'
                                                        ] = use_id_external_id[uCid]
                                            # property_building_type_id
                                            if 'buildingType' in property:
                                                buildingType = property['buildingType']
                                                if 'id' in buildingType:
                                                    bTid = str(buildingType['id'])
                                                    bTname = buildingType['name']
                                                    bTname = bTname.encode('utf-8')
                                                    # if not exists create
                                                    if bTid not in bt_id_external_id:
                                                        type_vals = {
                                                            'external_id': bTid,
                                                            'name': bTname,
                                                        }
                                                        bt_obj = self.env[
                                                            model_p_b_t
                                                        ].sudo().create(type_vals)
                                                        # add_array
                                                        e_id = type_vals['external_id']
                                                        bt_id_external_id[
                                                            e_id
                                                        ] = bt_obj.id
                                                    # check_if_exists and add
                                                    if bTid in bt_id_external_id:
                                                        vals[
                                                            'property_building_type_id'
                                                        ] = bt_id_external_id[bTid]
                                            # create
                                            self.env[model_p_p].sudo().create(vals)
                                        # total_properties
                                        total_properties += 1
        else:
            _logger.info('status_code')
            _logger.info(response.status_code)
            _logger.info(url)
        # update date_last_check + total_properties
        self.date_last_check = current_date.strftime("%Y-%m-%d")
        self.total_properties = total_properties
        # return
        return return_item

    @api.model
    def cron_check_numbers(self):
        way_ids = self.env['property.way'].search(
            [
                ('full', '=', False)
            ]
        )
        if way_ids:
            count = 0
            for way_id in way_ids:
                count += 1
                # action_get_municipalities
                return_item = way_id.action_get_numbers()[0]
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
                    way_id.name.encode('utf-8'),
                    percent,
                    '%',
                    count,
                    len(way_ids)
                ))
                # update
                way_id.full = True
                # Sleep 1 second to prevent error (if request)
                time.sleep(1)
