# -*- coding: utf-8 -*-
#https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx?op=ConsultaProvincia
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz

class SedecatastroProvincia(models.Model):
    _name = 'sedecatastro.provincia'
    _description = 'Sedecatastro Provincia'
    
    cpine = fields.Char(
        string='Cpine',
        help='CODIGO INE DE LA PROVINCIA'
    )
    np = fields.Char(
        string='Np',
        help='NOMBRE DE LA PROVINCIA'
    )
    full = fields.Boolean(
        string='Full'
    )
    date_last_check = fields.Date(
        string='Date Last Check'
    )
    total_municipios = fields.Integer(
        string='Total municipios'
    )
    
    @api.one    
    def action_get_municipios_sedecatastro(self):
        current_date = datetime.now()
        #return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        #request
        url = 'http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/ConsultaMunicipio'
        data_obj = {
            'Provincia': self.np, 
            'Municipio': ''
        }                 
        response = requests.post(url, data=data_obj)        
        if response.status_code==200:
            xmltodict_response = xmltodict.parse(response.text)
            municipios = json.loads(json.dumps(xmltodict_response))            
            if 'consulta_municipiero' in municipios:                    
                if 'municipiero' in municipios['consulta_municipiero']:
                    if 'muni' in municipios['consulta_municipiero']['municipiero']:
                        #total_municipios
                        if 'control' in municipios['consulta_municipiero']:
                            if 'cumun' in municipios['consulta_municipiero']['control']:
                                self.total_municipios = municipios['consulta_municipiero']['control']['cumun']
                                #Fix 1
                                if municipios['consulta_municipiero']['control']['cumun']=="1":
                                    municipios['consulta_municipiero']['municipiero']['muni'] = [municipios['consulta_municipiero']['municipiero']['muni']]                                                                
                        #for
                        for muni_item in municipios['consulta_municipiero']['municipiero']['muni']:
                            sedecatastro_municipio_ids = self.env['sedecatastro.municipio'].search(
                                [
                                    ('sedecatastro_provincia_id', '=', self.id), 
                                    ('loine_cm', '=', str(muni_item['loine']['cm']))
                                ]
                            )                            
                            if len(sedecatastro_municipio_ids)==0:
                                #creamos
                                sedecatastro_municipio_vals = {
                                    'sedecatastro_provincia_id': self.id,
                                    'nm': str(muni_item['nm'].encode('utf-8')),
                                    'locat_cd': str(muni_item['locat']['cd']),
                                    'locat_cmc': str(muni_item['locat']['cmc']),
                                    'loine_cp': str(muni_item['loine']['cp']),
                                    'loine_cm': str(muni_item['loine']['cm']),
                                    'total_vias': 0
                                }
                                sedecatastro_municipio_obj = self.env['sedecatastro.municipio'].sudo().create(sedecatastro_municipio_vals)
                        #update date_last_check
                        self.date_last_check = current_date.strftime("%Y-%m-%d")
            else:
                return {
                    'errors': True,
                    'status_code': response.status_code,
                    'error': {                        
                        'url': url,
                        'data': data_obj,
                        'text': municipios
                    }
                }                        
        else:
            return {
                'errors': True,
                'status_code': response.status_code,
                'error': {                    
                    'url': url,
                    'data': data_obj,
                    'text': response.text
                }
            }
        #return
        return return_item            
    
    @api.multi    
    def cron_check_sedecatastro_provincias(self, cr=None, uid=False, context=None):
        _logger.info('cron_check_sedecatastro_provincias')                        
        #request
        url = 'http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/ConsultaProvincia'
        response = requests.post(url, data={})
        
        if response.status_code!=200:
            xmltodict_response = xmltodict.parse(response.text)
            provincias = json.loads(json.dumps(xmltodict_response))        
            if 'consulta_provinciero' in provincias:
                if 'provinciero' in provincias['consulta_provinciero']:
                    if 'prov' in provincias['consulta_provinciero']['provinciero']:
                        for prov_item in provincias['consulta_provinciero']['provinciero']['prov']:
                            sedecatastro_provincia_ids = self.env['sedecatastro.provincia'].search([('cpine', '=', str(prov_item['cpine']))])
                            if len(sedecatastro_provincia_ids)==0:
                                #creamos
                                sedecatastro_provincia_vals = {
                                    'cpine': str(prov_item['cpine']),
                                    'np': str(prov_item['np'].encode('utf-8')),
                                    'total_municipios': 0
                                }
                                sedecatastro_provincia_obj = self.env['sedecatastro.provincia'].sudo().create(sedecatastro_provincia_vals)
            else:
                return_item = {
                    'errors': True,
                    'status_code': response.status_code,
                    'error': {                        
                        'url': url,
                        'text': response.text
                    }
                }                                
        else:
            return_item = {
                'errors': True,
                'status_code': response.status_code,
                'error': {                    
                    'url': url,
                    'text': response.text
                }
            }
        #_logger
        _logger.info(return_item)                                