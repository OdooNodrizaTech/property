# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# https://ovc.catastro.meh.es/
# /ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx?op=ConsultaProvincia
import logging
from odoo import api, fields, models
import requests
import xmltodict
import json
from datetime import datetime
_logger = logging.getLogger(__name__)


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

    @api.multi
    def action_get_municipios_sedecatastro(self):
        self.ensure_one()
        current_date = datetime.now()
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # request
        url = 'http://%s/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/%s' % (
            'ovc.catastro.meh.es',
            'ConsultaMunicipio'
        )
        data_obj = {
            'Provincia': self.np,
            'Municipio': ''
        }
        response = requests.post(url, data=data_obj)
        if response.status_code == 200:
            xmltodict_response = xmltodict.parse(response.text)
            municipios = json.loads(json.dumps(xmltodict_response))
            if 'consulta_municipiero' in municipios:
                consulta_municipiero = municipios['consulta_municipiero']
                if 'municipiero' in consulta_municipiero:
                    municipiero = consulta_municipiero['municipiero']
                    if 'muni' in municipiero:
                        muni = municipiero['muni']
                        # total_municipios
                        if 'control' in consulta_municipiero:
                            control = consulta_municipiero['control']
                            if 'cumun' in control:
                                cumun = control['cumun']
                                self.total_municipios = cumun
                                # Fix 1
                                if cumun == "1":
                                    muni = [muni]
                        # for
                        for muni_item in muni:
                            municipio_ids = self.env['sedecatastro.municipio'].search(
                                [
                                    ('sedecatastro_provincia_id', '=', self.id),
                                    ('loine_cm', '=', str(muni_item['loine']['cm']))
                                ]
                            )
                            if len(municipio_ids) == 0:
                                # creamos
                                vals = {
                                    'sedecatastro_provincia_id': self.id,
                                    'nm': str(muni_item['nm'].encode('utf-8')),
                                    'locat_cd': str(muni_item['locat']['cd']),
                                    'locat_cmc': str(muni_item['locat']['cmc']),
                                    'loine_cp': str(muni_item['loine']['cp']),
                                    'loine_cm': str(muni_item['loine']['cm']),
                                    'total_vias': 0
                                }
                                self.env['sedecatastro.municipio'].sudo().create(vals)
                        # update date_last_check
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
        # return
        return return_item

    @api.model
    def cron_check_sedecatastro_provincias(self):
        # request
        url = 'http://%s/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/%s' % (
            'ovc.catastro.meh.es',
            'ConsultaProvincia'
        )
        response = requests.post(url, data={})
        if response.status_code != 200:
            xmltodict_response = xmltodict.parse(response.text)
            provincias = json.loads(json.dumps(xmltodict_response))
            if 'consulta_provinciero' in provincias:
                consulta_provinciero = provincias['consulta_provinciero']
                if 'provinciero' in consulta_provinciero:
                    provinciero = consulta_provinciero['provinciero']
                    if 'prov' in provinciero:
                        prov = provinciero['prov']
                        for prov_item in prov:
                            provincia_ids = self.env['sedecatastro.provincia'].search(
                                [
                                    ('cpine', '=', str(prov_item['cpine']))
                                ]
                            )
                            if len(provincia_ids) == 0:
                                # creamos
                                vals = {
                                    'cpine': str(prov_item['cpine']),
                                    'np': str(prov_item['np'].encode('utf-8')),
                                    'total_municipios': 0
                                }
                                self.env['sedecatastro.provincia'].sudo().create(vals)
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
        # _logger
        _logger.info(return_item)
