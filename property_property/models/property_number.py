# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time

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
            ('bbva','BBVA')                                      
        ],
        string='Source',
        default='bbva'
    )
    total_properties = fields.Integer(
        string='Total Properties'
    )        
        
    @api.one    
    def action_get_properties(self, tsec, property_use_id_external_id=False, property_building_type_id_external_id=False):
        current_date = datetime.now()
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # property_use_id_external_id
        if property_use_id_external_id == False:
            property_use_id_external_id = {}
            property_use_ids = self.env['property.use'].search([('id', '>', 0)])
            if len(property_use_ids)>0:
                for property_use_id in property_use_ids:
                    property_use_id_external_id[str(property_use_id.external_id)] = property_use_id.id            
        # property_building_type_id_external_id
        if property_building_type_id_external_id == False:
            property_building_type_id_external_id = {}
            property_building_type_ids = self.env['property.building.type'].search([('id', '>', 0)])
            if property_building_type_ids:
                for property_building_type_id in property_building_type_ids:
                    property_building_type_id_external_id[str(property_building_type_id.external_id)] = property_building_type_id.id                                
        # requests
        total_properties = 0
        url = 'https://www.bbva.es/ASO/streetMap/V02/provinces/%s/municipalities/%s/towns/%s/ways/%s/numbers/%s/' % (
            self.property_way_id.property_town_id.property_municipality_id.property_state_id.external_id,
            self.property_way_id.property_town_id.property_municipality_id.external_id,
            self.property_way_id.property_town_id.external_id,
            self.property_way_id.external_id,
            self.external_id
        )
        headers = {'tsec': str(tsec)}
        response = requests.get(url, headers=headers)            
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if 'provinces' in response_json:
                for province in response_json['provinces']:
                    if 'municipalities' in province:
                        for municipality in province['municipalities']:
                            if 'towns' in municipality:
                                for town in municipality['towns']:
                                    if 'ways' in town:
                                        for way in town['ways']:
                                            if 'numbers' in way:
                                                for number in way['numbers']:
                                                    # update_number_info
                                                    # inhabitantsHouseHoldRatio
                                                    if 'inhabitantsHouseHoldRatio' in number:
                                                        self.inhabitants_house_hold_ratio = number['inhabitantsHouseHoldRatio']
                                                    # houseHoldsNumber
                                                    if 'houseHoldsNumber' in number:
                                                        self.house_holds_number = number['houseHoldsNumber']
                                                    # floorsNumber
                                                    if 'floorsNumber' in number:
                                                        self.floors_number = number['floorsNumber']
                                                    # profesionalActivitiesNumber
                                                    if 'profesionalActivitiesNumber' in number:
                                                        self.profesional_activities_number = number['profesionalActivitiesNumber']
                                                    # companiesNumber
                                                    if 'companiesNumber' in number:
                                                        self.companies_number = number['companiesNumber']
                                                    # officeNumbers
                                                    if 'officeNumbers' in number:
                                                        self.office_numbers = number['officeNumbers']                                                                         
                                                    # commercialsNumber
                                                    if 'commercialsNumber' in number:
                                                        self.commercials_number = number['commercialsNumber']
                                                    # garagesNumber
                                                    if 'garagesNumber' in number:
                                                        self.garages_number = number['garagesNumber']
                                                    # properties
                                                    if 'properties' in number:
                                                        for property in number['properties']:
                                                            property_property_ids = self.env['property.property'].search(
                                                                [
                                                                    ('property_number_id', '=', self.id),
                                                                    ('external_id', '=', str(property['id']))
                                                                ]
                                                            )
                                                            if len(property_property_ids) == 0:
                                                                # creamos
                                                                vals = {
                                                                    'property_number_id': self.id,                                                    
                                                                    'external_id': str(property['id']),
                                                                    'source': 'bbva',
                                                                    'total_build_units': 0
                                                                }
                                                                # surfaceArea
                                                                if 'surfaceArea' in property:
                                                                    vals['surface_area'] = str(property['surfaceArea'])
                                                                # plotSurfaceArea
                                                                if 'plotSurfaceArea' in property:
                                                                    vals['plot_surface_area'] = int(property['plotSurfaceArea'])
                                                                # builtSurfaceArea
                                                                if 'builtSurfaceArea' in property:
                                                                    vals['built_surface_area'] = int(property['builtSurfaceArea'])
                                                                # coefficient
                                                                if 'coefficient' in property:
                                                                    vals['coefficient'] = str(property['coefficient'].replace(',', '.'))
                                                                # yearOld
                                                                if 'yearOld' in property:
                                                                    vals['year_old'] = int(property['yearOld'])
                                                                # buildingYear
                                                                if 'buildingYear' in property:
                                                                    vals['building_year'] = int(property['buildingYear'])
                                                                # reformYear
                                                                if 'reformYear' in property:
                                                                    vals['reform_year'] = int(property['reformYear'])
                                                                # plotRegistryId
                                                                if 'plotRegistryId' in property:
                                                                    vals['plot_registry_id'] = str(property['plotRegistryId'])
                                                                # property_user_id
                                                                if 'useCode' in property:
                                                                    if 'id' in property['useCode']:
                                                                        # if not exists create
                                                                        if str(property['useCode']['id']) not in property_use_id_external_id:
                                                                            property_use_vals = {
                                                                                'external_id': str(property['useCode']['id']),
                                                                                'name': str(property['useCode']['name'].encode('utf-8')),
                                                                            } 
                                                                            property_use_obj = self.env['property.use'].sudo().create(property_use_vals)
                                                                            # add_array
                                                                            property_use_id_external_id[str(property_use_vals['external_id'])] = property_use_obj.id
                                                                        # check_if_exists and add
                                                                        if str(property['useCode']['id']) in property_use_id_external_id:
                                                                            vals['property_user_id'] = property_use_id_external_id[str(property['useCode']['id'])]
                                                                # property_building_type_id
                                                                if 'buildingType' in property:
                                                                    if 'id' in property['buildingType']:
                                                                        # if not exists create
                                                                        if str(property['buildingType']['id']) not in property_building_type_id_external_id:
                                                                            property_building_type_vals = {
                                                                                'external_id': str(property['buildingType']['id']),
                                                                                'name': str(property['buildingType']['name'].encode('utf-8')),
                                                                            } 
                                                                            property_building_type_obj = self.env['property.building.type'].sudo().create(property_building_type_vals)
                                                                            # add_array
                                                                            property_building_type_id_external_id[str(property_building_type_vals['external_id'])] = property_building_type_obj.id
                                                                        # check_if_exists and add
                                                                        if str(property['buildingType']['id']) in property_building_type_id_external_id:
                                                                            vals['property_building_type_id'] = property_building_type_id_external_id[str(property['buildingType']['id'])]
                                                                # create
                                                                self.env['property.property'].sudo().create(vals)
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
    
    @api.multi    
    def cron_check_numbers(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_numbers')
        
        property_way_ids = self.env['property.way'].search([('full', '=', False)])
        if property_way_ids:
            count = 0
            for property_way_id in property_way_ids:
                count += 1
                # action_get_municipalities
                return_item = property_way_id.action_get_numbers()[0]
                if 'errors' in return_item:
                    if return_item['errors'] == True:
                        _logger.info(return_item)
                        # fix
                        if return_item['status_code'] != 403:
                            _logger.info(paramos)
                        else:
                            _logger.info('Raro que sea un 403 pero pasamos')
                # _logger
                percent = (float(count)/float(len(property_way_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s - %s%s (%s/%s)' % (
                    property_way_id.name.encode('utf-8'),
                    percent,
                    '%',
                    count,
                    len(property_way_ids)
                ))
                # update
                property_way_id.full = True
                # Sleep 1 second to prevent error (if request)
                time.sleep(1)