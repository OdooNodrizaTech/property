# -*- coding: utf-8 -*-
#https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx?op=ConsultaMunicipio
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz

class SedecatastroMunicipio(models.Model):
    _name = 'sedecatastro.municipio'
    _description = 'Sedecatastro Municipio'
    
    sedecatastro_provincia_id = fields.Many2one(
        comodel_name='sedecatastro.provincia',
        string='Sedecatastro Provincia'
    )
    nm = fields.Char(
        string='Nm',
        help='DENOMINACION DEL MUNICIPIO SEGUN M. DE HACIENDA Y ADMINISTRACIONES PUBLICAS'
    )
    locat_cd = fields.Integer(
        string='Locat Cd',
        help='CODIGO DE LA DELEGACION MHAP'
    )
    locat_cmc = fields.Integer(
        string='Locat Cmc',
        help='CODIGO DEL MUNICIPIO'
    )
    loine_cp = fields.Integer(
        string='Loine Cp',
        help='CODIGO DE LA PROVINCIA'
    )
    loine_cm = fields.Integer(
        string='Loine Cm',
        help='CODIGO DEL MUNICIPIO'
    )
    full = fields.Boolean(
        string='Full'
    )
    date_last_check = fields.Date(
        string='Date Last Check'
    )
    total_vias = fields.Integer(
        string='Total vias',
        help='NUMERO DE ITEMS DEVUELTOS EN LA LISTA CALLEJERO'
    )
    
    @api.one    
    def action_get_vias_sedecatastro(self):
        current_date = datetime.now()
        #return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        #request
        url = 'http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/ConsultaVia'
        data_obj = {
            'Provincia': self.sedecatastro_provincia_id.np, 
            'Municipio': self.nm, 
            'TipoVia': '', 
            'NombreVia': ''
        }                  
        response = requests.post(url, data=data_obj)        
        if response.status_code==200:
            xmltodict_response = xmltodict.parse(response.text)
            vias = json.loads(json.dumps(xmltodict_response))            
            if 'consulta_callejero' in vias:
                if 'callejero' in vias['consulta_callejero']:
                    if 'calle' in vias['consulta_callejero']['callejero']:
                        #total_vias
                        if 'control' in vias['consulta_callejero']:
                            if 'cuca' in vias['consulta_callejero']['control']:
                                self.total_vias = vias['consulta_callejero']['control']['cuca']
                                #Fix 1
                                if vias['consulta_callejero']['control']['cuca']=="1":
                                    vias['consulta_callejero']['callejero']['calle'] = [vias['consulta_callejero']['callejero']['calle']]
                        #for
                        for calle_item in vias['consulta_callejero']['callejero']['calle']:
                            sedecatastro_via_ids = self.env['sedecatastro.via'].search(
                                [
                                    ('sedecatastro_provincia_id', '=', self.sedecatastro_provincia_id.id),
                                    ('dir_cv', '=', str(calle_item['dir']['cv']))
                                ]
                            )
                            if len(sedecatastro_via_ids)==0:
                                #Fix dir tv
                                if type(calle_item['dir']['tv']) is dict:
                                    calle_item['dir']['tv'] = ''                                        
                                #creamos
                                sedecatastro_via_vals = {
                                    'sedecatastro_provincia_id': self.sedecatastro_provincia_id.id,
                                    'sedecatastro_municipio_id': self.id,
                                    'loine_cp': str(calle_item['loine']['cp']),
                                    'loine_cm': str(calle_item['loine']['cm']),
                                    'dir_cv': str(calle_item['dir']['cv']),
                                    'dir_tv': str(calle_item['dir']['tv'].encode('utf-8')),
                                    'dir_nv': str(calle_item['dir']['nv'].encode('utf-8')),                                        
                                }                                    
                                sedecatastro_via_obj = self.env['sedecatastro.via'].sudo().create(sedecatastro_via_vals)
                        #update date_last_check
                        self.date_last_check = current_date.strftime("%Y-%m-%d")
            else:
                return {
                    'errors': True,
                    'status_code': response.status_code,
                    'error': {                        
                        'url': url,
                        'data': data_obj,
                        'text': vias
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
    
    @api.model    
    def cron_check_sedecatastro_municipios(self):
        _logger.info('cron_check_sedecatastro_municipios')
        
        sedecatastro_provincia_ids = self.env['sedecatastro.provincia'].search([('full', '=', False)])
        if len(sedecatastro_provincia_ids)>0:
            count = 0
            for sedecatastro_provincia_id in sedecatastro_provincia_ids:
                count += 1
                #action_get_municipios_sedecatastro
                return_item = sedecatastro_provincia_id.action_get_municipios_sedecatastro()[0]
                if 'errors' in return_item:
                    if return_item['errors']==True:
                        _logger.info(return_item)
                        #fix
                        if return_item['status_code']!=403:
                            _logger.info(paramos)
                        else:
                            _logger.info('Raro que sea un 403 pero pasamos')
                #_logger                
                percent = (float(count)/float(len(sedecatastro_provincia_ids)))*100
                percent = "{0:.2f}".format(percent)                    
                _logger.info(str(sedecatastro_provincia_id.np.encode('utf-8'))+' - '+str(percent)+'% ('+str(count)+'/'+str(len(sedecatastro_provincia_ids))+')')                                        
                #update
                sedecatastro_provincia_id.full = True
                #Sleep 1 second to prevent error
                time.sleep(1)                                                