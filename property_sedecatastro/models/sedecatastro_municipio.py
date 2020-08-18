# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# https://ovc.catastro.meh.es/
# /ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx?op=ConsultaMunicipio
import logging
from odoo import api, fields, models, _
import requests
import xmltodict
import json
from datetime import datetime
import time
_logger = logging.getLogger(__name__)


class SedecatastroMunicipio(models.Model):
    _name = 'sedecatastro.municipio'
    _description = 'Sedecatastro Municipio'

    sedecatastro_provincia_id = fields.Many2one(
        comodel_name='sedecatastro.provincia',
        string='Sedecatastro Provincia'
    )
    nm = fields.Char(
        string='Nm',
        help='DENOMINACION DEL MUNICIPIO SEGUN M. DE HACIENDA Y ADMINI PUBLICAS'
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

    @api.multi
    def action_get_vias_sedecatastro(self):
        self.ensure_one()
        current_date = datetime.now()
        key_s_p_id = 'sedecatastro_provincia_id'
        key_s_m_id = 'sedecatastro_municipio_id'
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # request
        url = 'http://%s/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/%s' % (
            'ovc.catastro.meh.es',
            'ConsultaVia'
        )
        data_obj = {
            'Provincia': self.sedecatastro_provincia_id.np,
            'Municipio': self.nm,
            'TipoVia': '',
            'NombreVia': ''
        }
        response = requests.post(url, data=data_obj)
        if response.status_code == 200:
            xmltodict_response = xmltodict.parse(response.text)
            vias = json.loads(json.dumps(xmltodict_response))
            if 'consulta_callejero' in vias:
                consulta_callejero = vias['consulta_callejero']
                if 'callejero' in consulta_callejero:
                    if 'calle' in consulta_callejero['callejero']:
                        calle = consulta_callejero['callejero']['calle']
                        # total_vias
                        if 'control' in consulta_callejero:
                            control = consulta_callejero['control']
                            if 'cuca' in control:
                                self.total_vias = control['cuca']
                                # Fix 1
                                if control['cuca'] == "1":
                                    calle = [calle]
                        # for
                        for calle_item in calle:
                            sedecatastro_via_ids = self.env['sedecatastro.via'].search(
                                [
                                    (
                                        key_s_p_id,
                                        '=',
                                        self.sedecatastro_provincia_id.id
                                    ),
                                    ('dir_cv', '=', str(calle_item['dir']['cv']))
                                ]
                            )
                            if len(sedecatastro_via_ids) == 0:
                                # Fix dir tv
                                if type(calle_item['dir']['tv']) is dict:
                                    calle_item['dir']['tv'] = ''
                                # creamos
                                loine = calle_item['loine']
                                dir = calle_item['dir']
                                vals = {
                                    key_s_p_id: self.sedecatastro_provincia_id.id,
                                    key_s_m_id: self.id,
                                    'loine_cp': str(loine['cp']),
                                    'loine_cm': str(loine['cm']),
                                    'dir_cv': str(dir['cv']),
                                    'dir_tv': str(dir['tv'].encode('utf-8')),
                                    'dir_nv': str(dir['nv'].encode('utf-8')),
                                }
                                self.env['sedecatastro.via'].sudo().create(vals)
                        # update date_last_check
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
        # return
        return return_item

    @api.model
    def cron_check_sedecatastro_municipios(self):
        provincia_ids = self.env['sedecatastro.provincia'].search(
            [
                ('full', '=', False)
            ]
        )
        if provincia_ids:
            count = 0
            for provincia_id in provincia_ids:
                count += 1
                # action_get_municipios_sedecatastro
                return_item = provincia_id.action_get_municipios_sedecatastro()[0]
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
                percent = (float(count)/float(len(provincia_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s - %s%s (%s/%s)' % (
                    provincia_id.np.encode('utf-8'),
                    percent,
                    '%',
                    count,
                    len(provincia_ids)
                ))
                # update
                provincia_id.full = True
                # Sleep 1 second to prevent error
                time.sleep(1)
