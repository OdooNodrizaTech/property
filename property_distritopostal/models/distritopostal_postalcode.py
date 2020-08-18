# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models, _
import requests
from bs4 import BeautifulSoup
_logger = logging.getLogger(__name__)


class DistritopostalPostalcode(models.Model):
    _name = 'distritopostal.postalcode'
    _description = 'Distritopostal Postalcode'

    distritopostal_municipality_id = fields.Many2one(
        comodel_name='distritopostal.municipality',
        string='Distritopostal Municipality Id'
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

    @api.multi
    def action_get_ways(self):
        self.ensure_one()
        model_d_w = 'distritopostal.way'
        key_d_m_id = 'distritopostal_municipality_id'
        key_d_p_id = 'distritopostal_postalcode_id'
        d_m_id = self.distritopostal_municipality_id
        url = 'http://distritopostal.es%s' % self.url
        response = requests.get(url)
        if response.status_code == 200:
            _logger.info(url)
            soup = BeautifulSoup(response.text, 'lxml')
            # tiene_calles
            change_full = False
            tiene_calles = False
            h2_items = soup.findAll('h2')
            for h2_item in h2_items:
                if 'Callejero de' in h2_item.text:
                    tiene_calles = True

            if not tiene_calles:
                _logger.info('No tiene calles, continuamos')
                # revisar numero de tablas
                table_items = soup.findAll('table')
                _logger.info('Tablas encontradas: '+str(len(table_items)))
                _logger.info(
                    _('Tablas encontradas: %s') % len(table_items)
                )
                if len(table_items) == 0:
                    _logger.info(
                        _('MUY RARO que un codigo postal no tenga ninguna '
                          'tabla PERO podria ser')
                    )
                    # change_full
                    change_full = True
                elif len(table_items) == 1:
                    _logger.info(
                        _('RARO SI, pero si solo tiene 1 tabla la web es que no '
                          'tiene calles este codigo postal por el motivo que sea, '
                          'lo damos por "bueno"')
                    )
                    # change_full
                    change_full = True
                else:
                    table_ids_check = []
                    if len(table_items) == 3:
                        _logger.info(
                            _('PARECE que las 2 tablas ultimas son las calles')
                        )
                        # operations
                        table_ids_check = [1, 2]
                        # change_full
                        change_full = True
                    else:
                        _logger.info(
                            _('PARECE que tiene varias tablas por municipio, revisamos '
                              'cual le corresponde de verdad')
                        )
                        _logger.info(
                            _('Buscamos la url =%s') % d_m_id.url
                        )
                        # operations
                        h3_items = soup.findAll('h3')
                        count = 0
                        for h3_item in h3_items:
                            h3_item_as = h3_item.findAll('a')
                            if len(h3_item_as) > 0:
                                h3_item_a = h3_item_as[0]
                                h3_item_href = str(h3_item_a.get('href'))
                                # check if is it
                                if str(h3_item_href) == str(d_m_id.url):
                                    table_ids_check.append(count)
                                    table_ids_check.append(count+1)
                            # sum
                            count += 2
                        # fix
                        names_related = {
                            '27677': [0, 1],
                            '37449': [2],
                            '37129': [2],
                            '32135': [0, 1],
                            '32137': [0, 1],
                            '01207': [2, 3],
                            '37111': [4],
                            '33127': [2, 3],
                            '32720': [0, 1],
                            '01206': [0, 1],
                            '27373': [0, 1],
                            '37186': [0, 1],
                            '37460': [4, 5],
                            '01520': [0, 1],
                            '01192': [0, 1],
                            '37193': [0, 1],
                            '37185': [4, 5],
                            '37209': [4, 5],
                            '33813': [0, 1],
                            '37139': [0],
                            '15686': [2, 3],
                            '37115': [6, 7],
                            '15689': [0, 1],
                            '37609': [4, 5]
                        }
                        table_ids_check = names_related[self.name]
                        # table_ids_check
                        _logger.info('table_ids_check')
                        _logger.info(table_ids_check)
                        # change_full
                        change_full = True
                    # operations table_ids_check
                    if len(table_ids_check) == 0:
                        _logger.info(
                            _('MUY MUY RARO no encontrar ninguna tabla a comprobar')
                        )
                        # Fix raro
                        change_full = False
                    else:
                        for table_id_check in table_ids_check:
                            table_item_need_check = None
                            # check_table_id_check
                            count = 0
                            for table_item in table_items:
                                if table_id_check == count:
                                    table_item_need_check = table_item
                                # sum
                                count += 1
                            # operations
                            if table_item_need_check is None:
                                _logger.info(
                                    _('RARO, no existe la tabla con indice %s')
                                    % table_id_check
                                )
                                # Fix raro
                                change_full = False
                            else:
                                table_item = table_item_need_check
                                table_item_trs = table_item.findAll('tr')
                                if len(table_item_trs) > 1:
                                    # _logger.info(table_item_trs)
                                    table_item_tr_1 = table_item_trs[1]
                                    table_item_tr_1_tds = table_item_tr_1.findAll('td')
                                    # fix la tabla buena
                                    if len(table_item_tr_1_tds) == 4:
                                        for item_tr in table_item_trs:
                                            table_item_tr_tds = item_tr.findAll('td')
                                            if len(table_item_tr_tds) > 0:
                                                td_0 = table_item_tr_tds[0]
                                                # calle_nombre
                                                calle_nombre = str(
                                                    td_0.text.encode('utf-8')
                                                )
                                                # search
                                                way_ids = self.env[model_d_w].search(
                                                    [
                                                        (key_d_m_id, '=', d_m_id.id),
                                                        ('name', '=', calle_nombre)
                                                    ]
                                                )
                                                if len(way_ids) == 0:
                                                    # vals
                                                    vals = {
                                                        key_d_m_id: d_m_id.id,
                                                        key_d_p_id: self.id,
                                                        'name': str(calle_nombre)
                                                    }
                                                    # create
                                                    self.env[model_d_w].sudo().create()
            else:
                _logger.info(
                    _('SI tiene calles, continuamos')
                )
                # operations
                div_datatab_items = soup.findAll('div', {"class": "datatab"})
                # table_items = soup.findAll('table')
                for div_datatab_item in div_datatab_items:
                    table_items = div_datatab_item.findAll('table')
                    for table_item in table_items:
                        table_item_trs = table_item.findAll('tr')
                        if len(table_item_trs) > 1:
                            # _logger.info(table_item_trs)
                            table_item_tr_1 = table_item_trs[1]
                            table_item_tr_1_tds = table_item_tr_1.findAll('td')
                            # fix la tabla buena
                            if len(table_item_tr_1_tds) == 4:
                                for table_item_tr in table_item_trs:
                                    table_item_tr_tds = table_item_tr.findAll('td')
                                    if len(table_item_tr_tds) > 0:
                                        td_0 = table_item_tr_tds[0]
                                        # calle_nombre
                                        calle_nombre = str(td_0.text.encode('utf-8'))
                                        # search
                                        way_ids = self.env[model_d_w].search(
                                            [
                                                (key_d_m_id, '=', d_m_id.id),
                                                ('name', '=', calle_nombre)
                                            ]
                                        )
                                        if len(way_ids) == 0:
                                            # vals
                                            vals = {
                                                key_d_m_id : d_m_id.id,
                                                key_d_p_id : self.id,
                                                'name': str(calle_nombre)
                                            }
                                            # create
                                            self.env[model_d_w].sudo().create(vals)
                # change_full
                change_full = True
            # change_full
            if change_full:
                self.full = True
