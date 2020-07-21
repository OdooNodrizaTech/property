# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx?op=Consulta_DNPRC

from odoo import fields, models


class SedecatastroInmuebleConstruccion(models.Model):
    _name = 'sedecatastro.inmueble.construccion'
    _description = 'Sedecatastro Inmueble Construccion'
    
    sedecatastro_inmueble_id = fields.Many2one(
        comodel_name='sedecatastro.inmueble',
        string='Sedecatastro Inmueble'
    )    
    lcd = fields.Char(
        string='Lcd',
        help='USO DE LA UNIDAD CONSTRUCTIVA'
    )
    dt_lourb_loint_es = fields.Integer(
        string='Dt Lourb Loint Es',
        help='ESCLAERA'
    )
    dt_lourb_loint_pt = fields.Char(
        string='Dt Lourb Loint Pt',
        help='PLANTA'
    )
    dt_lourb_loint_pu = fields.Char(
        string='Dt Lourb Loint Pu',
        help='PUERTA'
    )
    dfcons_stl = fields.Integer(
        string='Dfcons Stl',
        help='SUPERFICIE DE LOS ELEMENTOS COMUNES'
    )