# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx?op=ConsultaVia
import logging
from odoo import api, fields, models, _
import requests
import xmltodict
import json
from datetime import datetime
import pytz
import urllib
import time
_logger = logging.getLogger(__name__)


class SedecatastroVia(models.Model):
    _name = 'sedecatastro.via'
    _description = 'Sedecatastro Via'

    sedecatastro_provincia_id = fields.Many2one(
        comodel_name='sedecatastro.provincia',
        string='Sedecatastro Provincia'
    )
    sedecatastro_municipio_id = fields.Many2one(
        comodel_name='sedecatastro.municipio',
        string='Sedecatastro Municipio'
    )
    loine_cp = fields.Integer(
        string='Loine Cp',
        help='CODIGO INE DE LA PROVINCIA'
    )
    loine_cm = fields.Integer(
        string='Loine Cm',
        help='CODIGO INE DEL MUNICIPIO'
    )
    dir_cv = fields.Char(
        string='Dir Cv',
        help='CODIGO DE LA VIA SEGUN DGC'
    )
    dir_tv = fields.Char(
        string='Dir Tv',
        help='CODIFICACION DEL TIPO DE ViA (ANEXO I)'
    )
    dir_nv = fields.Char(
        string='Dir Nv',
        help='DENOMINACION DE LA VIA SEGUN DGC'
    )
    full = fields.Boolean(
        string='Full'
    )
    date_last_check = fields.Date(
        string='Date Last Check'
    )
    last_number_know = fields.Integer(
        string='Last Number Know'
    )

    @api.multi
    def action_get_numeros_sedecatastro(self):
        self.ensure_one()
        current_date = datetime.now(pytz.timezone('Europe/Madrid'))
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # operations
        continue_check_numbers = True
        numero = 0
        numero_request = 5
        # while
        while continue_check_numbers:
            # pruebas_get
            url = 'http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/ConsultaNumero'
            params_url = {
                'Provincia': str(self.sedecatastro_provincia_id.np),
                'Municipio': str(self.sedecatastro_municipio_id.nm.encode('utf-8')),
                'tipoVia': str(self.dir_tv),
                'NomVia': str(self.dir_nv.encode('utf-8')),
                'Numero': numero_request
            }
            url_partial = urllib.urlencode(params_url)
            url += '?%s' % url_partial
            response = requests.get(url)
            if response.status_code == 200:
                try:
                    xmltodict_response = xmltodict.parse(response.text)
                    numeros = json.loads(json.dumps(xmltodict_response))
                    numero_has_changed = False
                    # consulta_numerero
                    if 'consulta_numerero' in numeros:
                        # total
                        if 'control' in numeros['consulta_numerero']:
                            if 'cunum' in numeros['consulta_numerero']['control']:
                                # Fix 1
                                if numeros['consulta_numerero']['control']['cunum'] == "1":
                                    numeros['consulta_numerero']['numerero']['nump'] = [numeros['consulta_numerero']['numerero']['nump']]
                                    continue_check_numbers = False
                        # items
                        if 'numerero' in numeros['consulta_numerero']:
                            if 'nump' in numeros['consulta_numerero']['numerero']:
                                # for
                                for nump_item in numeros['consulta_numerero']['numerero']['nump']:
                                    numero_item = int(nump_item['num']['pnp'])
                                    if numero_item > numero:
                                        numero = numero_item
                                        numero_has_changed = True
                                    # params
                                    finca_item = str(nump_item['pc']['pc1'])
                                    hoja_plano_item = str(nump_item['pc']['pc2'])
                                    numero_ids = self.env['sedecatastro.numero'].search(
                                        [
                                            ('sedecatastro_municipio_id', '=', self.id),
                                            ('numero', '=', str(numero_item)),
                                            ('finca', '=', str(finca_item)),
                                            ('hoja_plano', '=', str(hoja_plano_item))
                                        ]
                                    )
                                    if len(numero_ids) == 0:
                                        vals = {
                                            'sedecatastro_provincia_id': self.sedecatastro_provincia_id.id,
                                            'sedecatastro_municipio_id': self.sedecatastro_municipio_id.id,
                                            'sedecatastro_via_id': self.id,
                                            'numero': numero_item,
                                            'finca': finca_item,
                                            'hoja_plano': hoja_plano_item,
                                        }
                                        self.env['sedecatastro.numero'].sudo().create(vals)
                    else:
                        return {
                            'errors': True,
                            'status_code': response.status_code,
                            'error': {
                                'params': params_url,
                                'url': url,
                                'text': numeros
                            }
                        }
                    # numero_has_changed
                    if not numero_has_changed:
                        continue_check_numbers = False
                    else:
                        numero_request = numero+5
                        time.sleep(1)
                except:
                    return {
                        'errors': True,
                        'status_code': response.status_code,
                        'error': {
                            'params': params_url,
                            'url': url,
                            'text': response.text
                        }
                    }                                                                                    
            else:
                return {
                    'errors': True,
                    'status_code': response.status_code,
                    'error': {
                        'params': params_url,
                        'url': url,
                        'text': response.text
                    }
                }
        # update
        self.last_number_know = numero
        self.date_last_check = current_date.strftime("%Y-%m-%d")
        # return
        return return_item

    @api.model
    def cron_check_sedecatastro_vias(self):
        municipio_ids = self.env['sedecatastro.municipio'].search(
            [
                ('full', '=', False)
            ]
        )
        if municipio_ids:
            count = 0
            for municipio_id in municipio_ids:
                count += 1
                # action_get_vias_sedecatastro
                return_item = municipio_id.action_get_vias_sedecatastro()[0]
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
                # _logger.info(sedecatastro_municipio_id.nm)
                percent = (float(count)/float(len(municipio_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s - %s%s (%s/%s)' % (
                    municipio_id.nm.encode('utf-8'),
                    percent,
                    '%',
                    count,
                    len(municipio_ids)
                ))
                # update
                municipio_id.full = True
                # Sleep 1 second to prevent error
                time.sleep(1)
