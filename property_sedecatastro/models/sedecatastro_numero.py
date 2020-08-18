# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# https://ovc.catastro.meh.es/
# /ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx?op=ConsultaNumero
import logging
from odoo import api, fields, models, _
import requests
import xmltodict
import json
from datetime import datetime
import time
_logger = logging.getLogger(__name__)


class SedecatastroNumero(models.Model):
    _name = 'sedecatastro.numero'
    _description = 'Sedecatastro Numero'

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
    numero = fields.Integer(
        string='Numero'
    )
    finca = fields.Char(
        string='Finca'
    )
    hoja_plano = fields.Char(
        string='Hoja Plano'
    )
    full = fields.Boolean(
        string='Full'
    )
    date_last_check = fields.Date(
        string='Date Last Check'
    )
    total_inmuebles = fields.Integer(
        string='Total inmuebles'
    )

    @api.multi
    def action_get_inmuebles_sedecatastro(self):
        self.ensure_one()
        current_date = datetime.now()
        model_s_i = 'sedecatastro.inmueble'
        model_s_i_c = 'sedecatastro.inmueble.construccion'
        key_s_p_id = 'sedecatastro_provincia_id'
        key_s_m_id = 'sedecatastro_municipio_id'
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # fields_to_create_reference
        fields_to_create_reference = ['rc_pc1', 'rc_pc2', 'rc_car', 'rc_cc1', 'rc_cc2']
        # request
        url = 'http://%s/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/%s' % (
            'ovc.catastro.meh.es',
            'Consulta_DNPRC'
        )
        data_obj = {
            'Provincia': self.sedecatastro_provincia_id.np,
            'Municipio': self.sedecatastro_municipio_id.nm,
            'RC': str(self.finca)+str(self.hoja_plano),
        }
        response = requests.post(url, data=data_obj)
        if response.status_code == 200:
            xmltodict_response = xmltodict.parse(response.text)
            inmuebles = json.loads(json.dumps(xmltodict_response))
            # _logger.info(inmuebles)
            if 'consulta_dnp' in inmuebles:
                consulta_dnp = inmuebles['consulta_dnp']
                # total_inmuebles
                if 'control' in consulta_dnp:
                    control = consulta_dnp['control']
                    self.total_inmuebles = int(control['cudnp'])
                # inmueble y toda la info
                if 'bico' in consulta_dnp:
                    bico = consulta_dnp['bico']
                    if 'bi' in bico:
                        bi = bico['bi']
                        # vals
                        vals = {
                            key_s_p_id: self.sedecatastro_provincia_id.id,
                            key_s_m_id: self.sedecatastro_municipio_id.id,
                            'sedecatastro_via_id': self.sedecatastro_via_id.id,
                            'sedecatastro_numero_id': self.id,
                            'referencia': '',
                            'date_last_check': current_date.strftime("%Y-%m-%d"),
                            'full': True,
                            'ldt': str(bi['ldt'].encode('utf-8'))
                        }
                        # idbi
                        if 'idbi' in bi:
                            idbi = bi['idbi']
                            vals['idbi_cn'] = str(idbi['cn'])
                            # rc
                            if 'rc' in idbi:
                                rc = idbi['rc']
                                vals['rc_pc1'] = str(rc['pc1'])
                                vals['rc_pc2'] = str(rc['pc2'])
                                vals['rc_car'] = str(rc['car'])
                                vals['rc_cc1'] = str(rc['cc1'])
                                vals['rc_cc2'] = str(rc['cc2'])
                        # debi
                        if 'debi' in bi:
                            debi = bi['debi']
                            # luso
                            if 'luso' in debi:
                                vals['debi_luso'] = str(debi['luso'].encode('utf-8'))
                            # sfc
                            if 'sfc' in debi:
                                vals['debi_sfc'] = int(debi['sfc'])
                            # cpt
                            if 'cpt' in debi:
                                vals['debi_cpt'] = str(debi['cpt'].replace(',', '.'))
                            # ant
                            if 'ant' in debi:
                                vals['debi_ant'] = int(debi['ant'])
                        # referencia
                        for field in fields_to_create_reference:
                            if field in vals:
                                vals['referencia'] += str(vals[field])
                        # create if not exists
                        inmueble_ids = self.env[model_s_i].search(
                            [
                                ('sedecatastro_numero_id', '=', self.id),
                                ('referencia', '=', str(vals['referencia']))
                            ]
                        )
                        if len(inmueble_ids) == 0:
                            inmueble_obj = self.env[model_s_i].sudo().create(vals)
                            # lcons
                            if 'lcons' in bico:
                                lcons = bico['lcons']
                                if 'cons' in lcons:
                                    cons = lcons['cons']
                                    # fix multi items
                                    if type(cons) == dict:
                                        cons = [cons]
                                    # for
                                    for con_item in cons:
                                        # cals
                                        vals = {
                                            'sedecatastro_inmueble_id': inmueble_obj.id,
                                            'lcd': str(con_item['lcd'])
                                        }
                                        # dt
                                        if 'dt' in con_item:
                                            dt = con_item['dt']
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
                                        if 'dfcons' in con_item:
                                            dfcons = con_item['dfcons']
                                            vals['dfcons_stl'] = int(dfcons['stl'])
                                        # create
                                        self.env[model_s_i_c].sudo().create(vals)
                # listado de inmuebles, guardamos pero habra que volver a consultarle
                if 'lrcdnp' in consulta_dnp:
                    lrcdnp = consulta_dnp['lrcdnp']
                    if 'rcdnp' in lrcdnp:
                        rcdnp = lrcdnp['rcdnp']
                        for rcdnp_item in rcdnp:
                            if 'rc' in rcdnp_item:
                                # vals
                                vals = {
                                    key_s_p_id: self.sedecatastro_provincia_id.id,
                                    key_s_m_id: self.sedecatastro_municipio_id.id,
                                    'sedecatastro_via_id': self.sedecatastro_via_id.id,
                                    'sedecatastro_numero_id': self.id,
                                    'referencia': '',
                                    'rc_pc1': str(rcdnp_item['rc']['pc1']),
                                    'rc_pc2': str(rcdnp_item['rc']['pc2']),
                                    'rc_car': str(rcdnp_item['rc']['car']),
                                    'rc_cc1': str(rcdnp_item['rc']['cc1']),
                                    'rc_cc2': str(rcdnp_item['rc']['cc2'])
                                }
                                # referencia
                                for field in fields_to_create_reference:
                                    if field in vals:
                                        vals['referencia'] += str(vals[field])
                                # create if not exists
                                self.env['sedecatastro.inmueble'].sudo().create(vals)
                # update date_last_check
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
    def cron_check_sedecatastro_numeros(self):
        via_ids = self.env['sedecatastro.via'].search(
            [
                ('full', '=', False)
            ],
            limit=1000
        )
        if via_ids:
            count = 0
            for via_id in via_ids:
                count += 1
                # action_get_numeros_sedecatastro
                return_item = via_id.action_get_numeros_sedecatastro()[0]
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
                # _logger.info(sedecatastro_via_id.dir_nv)
                percent = (float(count)/float(len(via_ids)))*100
                percent = "{0:.2f}".format(percent)
                _logger.info('%s - %s%s (%s/%s)' % (
                    via_id.id,
                    percent,
                    '%',
                    count,
                    len(via_ids)
                ))
                # update
                via_id.full = True
                # Sleep 1 second to prevent error
                time.sleep(1)
