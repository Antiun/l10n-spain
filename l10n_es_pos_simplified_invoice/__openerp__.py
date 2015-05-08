# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright :
#        (c) 2014 Antiun Ingenieria S.L. (Madrid, Spain, http://www.antiun.com)
#                 Endika Iglesias <endikaig@antiun.com>
#                 Antonio Espinosa <antonioea@antiun.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Punto de venta con factura simplificada",
    "version": "1.0",
    "author": "Antiun Ingeniería S.L., "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Spanish Localization Team, "
              "Odoo Community Association (OCA)",
    "website": "http://www.antiun.com",
    "license": "AGPL-3",
    "category": "Point Of Sale",
    "description": """
Punto de venta con factura simplificada
================================

Adapta el terminal punto de venta a la legislación Española.
Adapta el ticket de venta a factura simplificada,
añadiendo el logo de la empresa y el NIF. E incluye los datos
del cliente (nombre, NIF y dirección).
Por último chequea que no se realice una factura simplificada con valor
superior a 400 euros.

    """,
    "depends": ['base', 'point_of_sale'],
    'data': [
        "views/pos_template.xml",
        "views/l10n_es_pos_simplified_invoice_report_receipt_report.xml",
    ],
    "qweb": [
        'static/src/xml/pos.xml',
    ],
    "installable": True,
}
