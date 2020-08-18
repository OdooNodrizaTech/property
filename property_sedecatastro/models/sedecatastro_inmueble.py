# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# https://ovc.catastro.meh.es/
# /ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx?op=Consulta_DNPRC
import logging
from odoo import api, fields, models, _
import requests
import xmltodict
import json
from datetime import datetime
import time
_logger = logging.getLogger(__name__)


class SedecatastroInmueble(models.Model):
    _name = 'sedecatastro.inmueble'
    _description = 'Sedecatastro Inmueble'

    sedecatastro_provincia_id = fields.Many2one(
        comodel_name='sedecatastro.provincia',
        string='Sedecatastro Provincia'
    )
    sedecatastro_municipio_id = fields.Many2one(
        comodel_name='sedecatastro.municipio',
        string='Sedecatastro Municipio'
    )
    sedecatastro_via_id = fields.Many2one(
        comodel_name='sedecatastro.via',
        string='Sedecatastro Via'
    )
    sedecatastro_numero_id = fields.Many2one(
        comodel_name='sedecatastro.numero',
        string='Sedecatastro Numero'
    )
    referencia = fields.Char(
        string='Referencia',
        help='Referencia Catastral (Concatenacion de todos los datos de rc)'
    )
    idbi_cn = fields.Char(
        string='Idbi Cn',
        help='TIPO DE BIEN INMUEBLE'
    )
    rc_pc1 = fields.Char(
        string='Rc Pc1',
        help='POSICIONES 1-7 DE LA REFERENCIA CATASTRAL (RC) DEL INMUEBLE'
    )
    rc_pc2 = fields.Char(
        string='Rc Pc2',
        help='POSICIONES 8-14 DE LA RC DEL INMUEBLE'
    )
    rc_car = fields.Char(
        string='Rc Car',
        help='POSICIONES 15-19 DE LA RC (CARGO)'
    )
    rc_cc1 = fields.Char(
        string='Rc Cc1',
        help='PRIMER DIGITO DE CONTROL DE LA RC'
    )
    rc_cc2 = fields.Char(
        string='Rc Cc2',
        help='SEGUNDO DIGITO DE CONTROL DE LA RC'
    )
    ldt = fields.Char(
        string='LDT',
        help='DOMICILIO TRIBUTARIO NO ESTRUCTURADO (TEXTO)'
    )
    debi_luso = fields.Char(
        string='Debi Luso',
        help='Residencial'
    )
    debi_sfc = fields.Integer(
        string='Debi Sfc',
        help='SUPERFICIE'
    )
    debi_cpt = fields.Float(
        string='Debi Cpt',
        help='COEFICIENTE DE PARTICIPACION'
    )
    debi_ant = fields.Integer(
        string='Debi Ant',
        help='ANTIGUEDAD'
    )
    full = fields.Boolean(
        string='Full'
    )
    date_last_check = fields.Date(
        string='Date Last Check'
    )

    @api.multi
    def action_get_info_sedecatastro(self):
        self.ensure_one()
        current_date = datetime.now()
        model_s_i_c = 'sedecatastro.inmueble.construccion'
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # request
        url = 'http://%s/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/%s' % (
            'ovc.catastro.meh.es',
            'Consulta_DNPRC'
        )
        data_obj = {
            'Provincia': self.sedecatastro_provincia_id.np,
            'Municipio': self.sedecatastro_municipio_id.nm,
            'RC': str(self.referencia)
        }
        response = requests.post(url, data=data_obj)
        if response.status_code == 200:
            xmltodict_response = xmltodict.parse(response.text)
            inmuebles = json.loads(json.dumps(xmltodict_response))
            if 'consulta_dnp' in inmuebles:
                consulta_dnp = inmuebles['consulta_dnp']
                if 'control' in consulta_dnp:
                    if consulta_dnp['control']['cudnp'] == '1':
                        # inmueble y toda la info
                        if 'bico' in consulta_dnp:
                            bico = consulta_dnp['bico']
                            _logger.info(
                                _('ok, es solo 1 inmueble con la info completa')
                            )
                            if 'bi' in bico:
                                bi = bico['bi']
                                # ldt
                                self.ldt = str(bi['ldt'].encode('utf-8'))
                                # idbi
                                if 'idbi' in bi:
                                    idbi = bi['idbi']
                                    self.idbi_cn = str(idbi['cn'])
                                    # rc
                                    if 'rc' in idbi:
                                        rc = idbi['rc']
                                        self.rc_pc1 = str(rc['pc1'])
                                        self.rc_pc2 = str(rc['pc2'])
                                        self.rc_car = str(rc['car'])
                                        self.rc_cc1 = str(rc['cc1'])
                                        self.rc_cc2 = str(rc['cc2'])
                                # debi
                                if 'debi' in bi:
                                    debi = bi['debi']
                                    # luso
                                    if 'luso' in debi:
                                        luso = debi['luso']
                                        self.debi_luso = str(luso.encode('utf-8'))
                                    # sfc
                                    if 'sfc' in debi:
                                        sfc = debi['sfc']
                                        self.debi_sfc = int(sfc)
                                    # cpt
                                    if 'cpt' in debi:
                                        cpt = debi['cpt']
                                        self.debi_cpt = str(cpt.replace(',', '.'))
                                    # ant
                                    if 'ant' in debi:
                                        ant = debi['ant']
                                        self.debi_ant = int(ant)
                                # lcons
                                if 'lcons' in bico:
                                    lcons = bico['lcons']
                                    if 'cons' in lcons:
                                        # fix multi items
                                        if type(lcons['cons']) == dict:
                                            lcons['cons'] = [lcons['cons']]
                                        # for
                                        for con in lcons['cons']:
                                            # cals
                                            vals = {
                                                'sedecatastro_inmueble_id': self.id,
                                                'lcd': str(con['lcd'])
                                            }
                                            # dt
                                            if 'dt' in con:
                                                dt = con['dt']
                                                if 'lourb' in dt:
                                                    lourb = dt['lourb']
                                                    if 'loint' in lourb:
                                                        loint = lourb['loint']
                                                        # es
                                                        if 'es' in loint:
                                                            vals[
                                                                'dt_lourb_loint_es'
                                                            ] = int(loint['es'])
                                                        # pt
                                                        if 'pt' in loint:
                                                            vals[
                                                                'dt_lourb_loint_pt'
                                                            ] = str(loint['pt'])
                                                        # pu
                                                        if 'pu' in loint:
                                                            vals[
                                                                'dt_lourb_loint_pu'
                                                            ] = str(loint['pu'])
                                            # dfcons
                                            if 'dfcons' in con:
                                                dfcons = con['dfcons']
                                                vals['dfcons_stl'] = int(dfcons['stl'])
                                            # create
                                            self.env[model_s_i_c].sudo().create(vals)
                        # finall_thins
                        self.full = True
                        self.date_last_check = current_date.strftime("%Y-%m-%d")
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
    def cron_check_sedecatastro_inmuebles(self):
        numero_ids = self.env['sedecatastro.numero'].search(
            [
                ('full', '=', False)
            ],
            limit=1000
        )
        if numero_ids:
            count = 0
            for numero_id in numero_ids:
                count += 1
                # action_get_numeros_sedecatastro
                return_item = numero_id.action_get_inmuebles_sedecatastro()[0]
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
                # _logger.info(sedecatastro_numero_id.id)
                percent = (float(count)/float(len(numero_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s - %s%s (%s/%s)' % (
                    numero_id.id,
                    percent,
                    '%',
                    count,
                    len(numero_ids)
                ))
                # update
                numero_id.full = True
                # Sleep 1 second to prevent error
                time.sleep(1)

    @api.model
    def cron_check_sedecatastro_inmuebles_sin_datos(self):
        inmueble_ids = self.env['sedecatastro.inmueble'].search(
            [
                ('full', '=', False)
            ],
            limit=1000
        )
        if inmueble_ids:
            count = 0
            for inmueble_id in inmueble_ids:
                count += 1
                # action_get_info_sedecatastro
                return_item = inmueble_id.action_get_info_sedecatastro()[0]
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
                # _logger.info(sedecatastro_inmueble_id.id)
                percent = (float(count)/float(len(inmueble_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s - %s%s (%s/%s)' % (
                    inmueble_id.id,
                    percent,
                    '%',
                    count,
                    len(inmueble_ids)
                ))
                # update
                inmueble_id.full = True
                # Sleep 1 second to prevent error
                time.sleep(1)
