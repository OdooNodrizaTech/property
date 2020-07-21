# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Ont Property Sedecatastro",
    "version": "12.0.1.0.0",
    "author": "Odoo Nodriza Tech (ONT)",
    "website": "https://nodrizatech.com/",
    "category": "Tools",
    "license": "AGPL-3",
    "depends": [
        "base"
    ],
    "external_dependencies": {
        "python3": [
            "xmltodict"
        ],
    },
    "data": [
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True
}