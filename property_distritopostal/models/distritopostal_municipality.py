# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time
from bs4 import BeautifulSoup

class DistritopostalMunicipality(models.Model):
    _name = 'distritopostal.municipality'
    _description = 'Distritopostal Municipality'
    
    distritopostal_state_id = fields.Many2one(
        comodel_name='distritopostal.state',
        string='Distritopostal State Id'
    )
    external_id = fields.Integer(
        string='External Id'
    )
    name = fields.Char(
        string='Name'
    )
    url = fields.Char(
        string='Url'
    )
    full = fields.Boolean(
        string='Full'
    )
    
    @api.one    
    def action_get_ways(self):
        url = 'http://distritopostal.es'+str(self.url)
        response = requests.get(url)
        if response.status_code==200:
            #_logger.info(response.text)                                                            
            soup = BeautifulSoup(response.text, 'lxml')
            #tiene_calles = False
            tiene_calles = False                    
            h2_items = soup.findAll('h2')
            for h2_item in h2_items:
                if 'Callejero de' in h2_item.text:
                    tiene_calles = True                     
            #tiene_calles
            if tiene_calles==False:
                _logger.info('no tiene calles, revisaremos para meter codigos postales')
                div_infocity_items = soup.findAll('div', {"class": "infocity"})
                for div_infocity_item in div_infocity_items:
                    h2_items = div_infocity_item.findAll('h2')
                    if len(h2_items)>0:
                        for h2_item in h2_items:
                            h2_item_as = h2_item.findAll('a')
                            if len(h2_item_as)>0:
                                h2_item_a_0 = h2_item_as[0]
                                h2_item_a_0_title = h2_item_a_0.get('title')                                                                                
                                if 'postales de la provincia de' not in h2_item_a_0_title:
                                    h2_item_a_0_href = str(h2_item_a_0.get('href'))
                                    #search
                                    distritopostal_postalcode_ids = self.env['distritopostal.postalcode'].search(
                                        [
                                            ('distritopostal_municipality_id', '=', self.id),
                                            ('url', '=', h2_item_a_0_href)
                                        ]
                                    )
                                    if len(distritopostal_postalcode_ids)==0:
                                        #vals
                                        distritopostal_postalcode_vals = {                                                    
                                            'distritopostal_municipality_id': self.id,
                                            'name': str(h2_item_a_0_href.replace('/', '')),
                                            'url': str(h2_item_a_0_href),                       
                                        }
                                        #create
                                        distritopostal_postalcode_obj = self.env['distritopostal.postalcode'].sudo().create(distritopostal_postalcode_vals)
                #update
                self.full = True                                                    
            else:
                div_datatab_items = soup.findAll('div', {"class": "datatab"})
                #table_items = soup.findAll('table')
                for div_datatab_item in div_datatab_items:
                    table_items = div_datatab_item.findAll('table')
                    for table_item in table_items:
                        table_item_trs = table_item.findAll('tr')
                        if len(table_item_trs)>1:
                            table_item_tr_1 = table_item_trs[1]
                            table_item_tr_1_tds = table_item_tr_1.findAll('td')
                            #fix la tabla buena
                            if len(table_item_tr_1_tds)==4:
                                for table_item_tr in table_item_trs:
                                    table_item_tr_tds = table_item_tr.findAll('td')
                                    if len(table_item_tr_tds)>0:
                                        #calle_nombre
                                        calle_nombre = str(table_item_tr_tds[0].text.encode('utf-8'))
                                        #search
                                        distritopostal_way_ids = self.env['distritopostal.way'].search(
                                            [
                                                ('distritopostal_municipality_id', '=', self.id),
                                                ('name', '=', calle_nombre)
                                            ]
                                        )
                                        if len(distritopostal_way_ids)==0:
                                            #vals
                                            distritopostal_way_vals = {                                                    
                                                'distritopostal_municipality_id': self.id,
                                                'name': str(calle_nombre)                       
                                            }
                                            #create
                                            distritopostal_way_obj = self.env['distritopostal.way'].sudo().create(distritopostal_way_vals)
                #update                                                
                self.full = True
    
    @api.multi    
    def cron_check_municipalities_distritopostal(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_municipalities_distritopostal')
        
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']        
        url = 'http://distritopostal.es/ajax/qmunicipio.php?term='
        for letter in letters:
            url_letter = url+str(letter)            
            response = requests.get(url_letter)
            if response.status_code==200:
                response_json = json.loads(response.text)
                for item in response_json:
                    distritopostal_municipality_ids = self.env['distritopostal.municipality'].search([('external_id', '=', item['lid'])])
                    if len(distritopostal_municipality_ids)==0:
                        #params
                        name = str(item['value'].encode('utf-8'))
                        name_split = name.split(',')
                        state = name_split[len(name_split)-1].strip()
                        #name remove state name
                        str_replace = ', '+str(state)
                        name = name.replace(str_replace, '').strip()               
                        #vals
                        distritopostal_municipality_vals = {                                                    
                            'external_id': item['lid'],
                            'name': str(name),
                            'url': str(item['url'])                        
                        }
                        #distritopostal_state_id
                        distritopostal_state_ids = self.env['distritopostal.state'].search([('name', '=', str(state))])
                        if len(distritopostal_state_ids)>0:
                            distritopostal_municipality_vals['distritopostal_state_id'] = distritopostal_state_ids[0].id
                        else:
                            #url_state
                            char_find = item['url'].rfind('/')
                            url_state = str(item['url'])[:char_find]
                            #vals
                            distritopostal_state_vals = {
                                'name': str(state),
                                'url': str(url_state),                      
                            }
                            distritopostal_state_obj = self.env['distritopostal.state'].sudo().create(distritopostal_state_vals)
                            distritopostal_municipality_vals['distritopostal_state_id'] = distritopostal_state_obj.id
                        #create
                        distritopostal_municipality_obj = self.env['distritopostal.municipality'].sudo().create(distritopostal_municipality_vals)