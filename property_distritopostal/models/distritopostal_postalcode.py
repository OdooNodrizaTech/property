# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

import requests, xmltodict, json
from datetime import datetime
import pytz
import time
from bs4 import BeautifulSoup

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
    
    @api.one    
    def action_get_ways(self):        
        url = 'http://distritopostal.es'+str(self.url)
        response = requests.get(url)
        if response.status_code==200:
            _logger.info(url)
            soup = BeautifulSoup(response.text, 'lxml')            
            #tiene_calles
            change_full = False
            tiene_calles = False                    
            h2_items = soup.findAll('h2')
            for h2_item in h2_items:
                if 'Callejero de' in h2_item.text:
                    tiene_calles = True
            
            if tiene_calles==False:
                _logger.info('No tiene calles, continuamos')
                #revisar numero de tablas
                table_items = soup.findAll('table')
                _logger.info('Tablas encontradas: '+str(len(table_items)))
                if len(table_items)==0:
                    _logger.info('MUY RARO que un codigo postal no tenga ninguna tabla PERO podria ser')
                    #change_full                        
                    change_full = True
                elif len(table_items)==1:
                    _logger.info('RARO SI, pero si solo tiene 1 tabla la web es que no tiene calles este codigo postal por el motivo que sea, lo damos por "bueno"')
                    #change_full
                    change_full = True
                else:
                    table_ids_check = []
                    if len(table_items)==3:
                        _logger.info('PARECE que las 2 tablas ultimas son las calles, procedemos')
                        #operations                        
                        table_ids_check = [1,2]                                                                
                        #change_full                        
                        change_full = True
                    else:
                        _logger.info('PARECE que tiene varias tablas por municipio, revisamos cual le corresponde de verdad')
                        _logger.info('Buscamos la url ='+str(self.distritopostal_municipality_id.url))
                        #operations
                        h3_items = soup.findAll('h3')
                        count = 0
                        for h3_item in h3_items:
                            h3_item_as = h3_item.findAll('a')
                            if len(h3_item_as)>0:
                                h3_item_a = h3_item_as[0]
                                h3_item_href = str(h3_item_a.get('href'))
                                #check if is it
                                if str(h3_item_href)==str(self.distritopostal_municipality_id.url):
                                    table_ids_check.append(count)
                                    table_ids_check.append(count+1)
                            #sum
                            count += 2
                        #fix
                        if self.name=='27677':
                            table_ids_check = [0,1]
                        elif self.name=='37449' or self.name=='37129':
                            table_ids_check = [2]
                        elif self.name=='32135' or self.name=='32137':
                            table_ids_check = [0,1]
                        elif self.name=='01207':
                            table_ids_check = [2,3]
                        elif self.name=='37111':                           
                           table_ids_check = [4]
                        elif self.name=='33127':                           
                           table_ids_check = [2,3]
                        elif self.name=='32720':                           
                           table_ids_check = [0,1]
                        elif self.name=='01206':                           
                           table_ids_check = [0,1]
                        elif self.name=='27373':                           
                           table_ids_check = [0,1]
                        elif self.name=='37186':                           
                           table_ids_check = [0,1]
                        elif self.name=='37460':                           
                           table_ids_check = [4,5]
                        elif self.name=='01520':                           
                           table_ids_check = [0,1]
                        elif self.name=='01192':                           
                           table_ids_check = [0,1]
                        elif self.name=='37193':                           
                           table_ids_check = [0,1]
                        elif self.name=='37185':                           
                           table_ids_check = [4,5]
                        elif self.name=='37209':                           
                           table_ids_check = [4,5]
                        elif self.name=='33813':                           
                           table_ids_check = [0,1]
                        elif self.name=='37139':                           
                           table_ids_check = [0]
                        elif self.name=='15686':                           
                           table_ids_check = [2,3]
                        elif self.name=='37115':                           
                           table_ids_check = [6,7]
                        elif self.name=='15689':                           
                           table_ids_check = [0,1]
                        elif self.name=='37609':                           
                           table_ids_check = [4,5]                                                                                                                                  
                        #table_ids_check                        
                        _logger.info('table_ids_check')                                                   
                        _logger.info(table_ids_check)
                        #change_full                        
                        change_full = True                            
                    #operations table_ids_check
                    if len(table_ids_check)==0:
                        _logger.info('MUY MUY RARO no encontrar ninguna tabla a comprobar')
                        #Fix raro
                        change_full = False
                    else:
                        for table_id_check in table_ids_check:
                            table_item_need_check = None
                            #check_table_id_check
                            count = 0
                            for table_item in table_items:
                                if table_id_check==count:
                                    table_item_need_check = table_item
                                #sum
                                count += 1
                            #operations
                            if table_item_need_check==None:
                                _logger.info('RARO, no existe la tabla con indice '+str(table_id_check))
                                #Fix raro
                                change_full = False
                            else:
                                table_item = table_item_need_check
                                table_item_trs = table_item.findAll('tr')
                                if len(table_item_trs)>1:
                                    #_logger.info(table_item_trs)
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
                                                        ('distritopostal_municipality_id', '=', self.distritopostal_municipality_id.id),
                                                        ('name', '=', calle_nombre)
                                                    ]
                                                )
                                                if len(distritopostal_way_ids)==0:
                                                    #vals
                                                    distritopostal_way_vals = {                                                    
                                                        'distritopostal_municipality_id': self.distritopostal_municipality_id.id,
                                                        'distritopostal_postalcode_id': self.id,
                                                        'name': str(calle_nombre)                       
                                                    }
                                                    #create
                                                    distritopostal_way_obj = self.env['distritopostal.way'].sudo().create(distritopostal_way_vals)
            else:
                _logger.info('SI tiene calles, continuamos')
                #operations
                div_datatab_items = soup.findAll('div', {"class": "datatab"})
                #table_items = soup.findAll('table')
                for div_datatab_item in div_datatab_items:
                    table_items = div_datatab_item.findAll('table')
                    for table_item in table_items:
                        table_item_trs = table_item.findAll('tr')
                        if len(table_item_trs)>1:
                            #_logger.info(table_item_trs)
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
                                                ('distritopostal_municipality_id', '=', self.distritopostal_municipality_id.id),
                                                ('name', '=', calle_nombre)
                                            ]
                                        )
                                        if len(distritopostal_way_ids)==0:
                                            #vals
                                            distritopostal_way_vals = {                                                    
                                                'distritopostal_municipality_id': self.distritopostal_municipality_id.id,
                                                'distritopostal_postalcode_id': self.id,
                                                'name': str(calle_nombre)                       
                                            }
                                            #create
                                            distritopostal_way_obj = self.env['distritopostal.way'].sudo().create(distritopostal_way_vals)                            
                #change_full                        
                change_full = True            
            #change_full
            if change_full==True:
                self.full = True            