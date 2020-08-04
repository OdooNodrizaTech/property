# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx?op=ConsultaNumero
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
        # return
        return_item = {
            'errors': False,
            'status_code': 200,
            'error': ''
        }
        # fields_to_create_reference
        fields_to_create_reference = ['rc_pc1', 'rc_pc2', 'rc_car', 'rc_cc1', 'rc_cc2']
        # request
        url = 'http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC'
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
                # total_inmuebles
                if 'control' in inmuebles['consulta_dnp']:
                    self.total_inmuebles = int(inmuebles['consulta_dnp']['control']['cudnp'])
                # inmueble y toda la info
                if 'bico' in inmuebles['consulta_dnp']:
                    if 'bi' in inmuebles['consulta_dnp']['bico']:
                        # vals
                        vals = {
                            'sedecatastro_provincia_id': self.sedecatastro_provincia_id.id,
                            'sedecatastro_municipio_id': self.sedecatastro_municipio_id.id,
                            'sedecatastro_via_id': self.sedecatastro_via_id.id,
                            'sedecatastro_numero_id': self.id,
                            'referencia': '',
                            'date_last_check': current_date.strftime("%Y-%m-%d"),
                            'full': True,
                            'ldt': str(inmuebles['consulta_dnp']['bico']['bi']['ldt'].encode('utf-8'))
                        }
                        # idbi
                        if 'idbi' in inmuebles['consulta_dnp']['bico']['bi']:
                            vals['idbi_cn'] = str(inmuebles['consulta_dnp']['bico']['bi']['idbi']['cn'])
                            # rc
                            if 'rc' in inmuebles['consulta_dnp']['bico']['bi']['idbi']:
                                vals['rc_pc1'] = str(inmuebles['consulta_dnp']['bico']['bi']['idbi']['rc']['pc1'])
                                vals['rc_pc2'] = str(inmuebles['consulta_dnp']['bico']['bi']['idbi']['rc']['pc2'])
                                vals['rc_car'] = str(inmuebles['consulta_dnp']['bico']['bi']['idbi']['rc']['car'])
                                vals['rc_cc1'] = str(inmuebles['consulta_dnp']['bico']['bi']['idbi']['rc']['cc1'])
                                vals['rc_cc2'] = str(inmuebles['consulta_dnp']['bico']['bi']['idbi']['rc']['cc2'])
                        # debi
                        if 'debi' in inmuebles['consulta_dnp']['bico']['bi']:
                            # luso
                            if 'luso' in inmuebles['consulta_dnp']['bico']['bi']['debi']:
                                vals['debi_luso'] = str(inmuebles['consulta_dnp']['bico']['bi']['debi']['luso'].encode('utf-8'))
                            # sfc
                            if 'sfc' in inmuebles['consulta_dnp']['bico']['bi']['debi']:
                                vals['debi_sfc'] = int(inmuebles['consulta_dnp']['bico']['bi']['debi']['sfc'])
                            # cpt
                            if 'cpt' in inmuebles['consulta_dnp']['bico']['bi']['debi']:
                                vals['debi_cpt'] = str(inmuebles['consulta_dnp']['bico']['bi']['debi']['cpt'].replace(',', '.'))
                            # ant
                            if 'ant' in inmuebles['consulta_dnp']['bico']['bi']['debi']:
                                vals['debi_ant'] = int(inmuebles['consulta_dnp']['bico']['bi']['debi']['ant'])
                        # referencia
                        for field_to_create_reference in fields_to_create_reference:
                            if field_to_create_reference in vals:
                                vals['referencia'] += str(vals[field_to_create_reference])
                        # create if not exists
                        inmueble_ids = self.env['sedecatastro.inmueble'].search(
                            [
                                ('sedecatastro_numero_id', '=', self.id),
                                ('referencia', '=', str(vals['referencia']))
                            ]
                        )
                        if len(inmueble_ids) == 0:
                            inmueble_obj = self.env['sedecatastro.inmueble'].sudo().create(vals)
                            # lcons
                            if 'lcons' in inmuebles['consulta_dnp']['bico']:
                                if 'cons' in inmuebles['consulta_dnp']['bico']['lcons']:
                                    # fix multi items
                                    if type(inmuebles['consulta_dnp']['bico']['lcons']['cons']) == dict:
                                        inmuebles['consulta_dnp']['bico']['lcons']['cons'] = [inmuebles['consulta_dnp']['bico']['lcons']['cons']]
                                    # for
                                    for cons_item in inmuebles['consulta_dnp']['bico']['lcons']['cons']:
                                        # cals
                                        vals = {
                                            'sedecatastro_inmueble_id': inmueble_obj.id,
                                            'lcd': str(cons_item['lcd'])
                                        }
                                        # dt
                                        if 'dt' in cons_item:
                                            if 'lourb' in cons_item['dt']:
                                                if 'loint' in cons_item['dt']['lourb']:
                                                    # es
                                                    if 'es' in cons_item['dt']['lourb']['loint']:
                                                        vals['dt_lourb_loint_es'] = int(cons_item['dt']['lourb']['loint']['es'])
                                                    # pt
                                                    if 'pt' in cons_item['dt']['lourb']['loint']:
                                                        vals['dt_lourb_loint_pt'] = str(cons_item['dt']['lourb']['loint']['pt'])
                                                    # pu
                                                    if 'pu' in cons_item['dt']['lourb']['loint']:
                                                        vals['dt_lourb_loint_pu'] = str(cons_item['dt']['lourb']['loint']['pu'])
                                        # dfcons
                                        if 'dfcons' in cons_item:
                                            vals['dfcons_stl'] = int(cons_item['dfcons']['stl'])
                                        # create
                                        self.env['sedecatastro.inmueble.construccion'].sudo().create(vals)
                # listado de inmuebles, guardamos pero habra que volver a consultarle
                if 'lrcdnp' in inmuebles['consulta_dnp']:
                    if 'rcdnp' in inmuebles['consulta_dnp']['lrcdnp']:
                        for rcdnp_item in inmuebles['consulta_dnp']['lrcdnp']['rcdnp']:
                            if 'rc' in rcdnp_item:
                                # vals
                                vals = {
                                    'sedecatastro_provincia_id': self.sedecatastro_provincia_id.id,
                                    'sedecatastro_municipio_id': self.sedecatastro_municipio_id.id,
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
                                for field_to_create_reference in fields_to_create_reference:
                                    if field_to_create_reference in vals:
                                        vals['referencia'] += str(vals[field_to_create_reference])
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
