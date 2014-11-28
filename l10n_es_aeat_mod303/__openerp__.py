# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) All rights reserved:
#       2014      Txerpa (https://www.txerpa.com)
#                 Biel Massot <biel.massot@txerpa.com>
#    Copyright del antiguo l10n_es_aeat_mod303 sobre el que esta realizado
#    este modulo
#       2013      Guadaltech (http://www.guadaltech.es)
#                 Alberto Martín Cortada
#       2014      Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                 Pedro M. Baeza <pedro.baeza@serviciobaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

{
    "name" : "Modelo 303 de la AEAT",
    "version" : "0.1",
    'author' : "Biel Massot <biel.massot@txerpa.com>",
    "license" : "AGPL-3",
    "website" : "https://www.txerpa.com",
    "description": "Modelo 303 de la AEAT",
    'contributors': [
        'Biel Massot <biel.massot@txerpa.com>',
        ],
    'category' : "Localisation/Accounting",
    "depends" : [
        "account",
        "l10n_es",
        "l10n_es_aeat",
        # "account_chart_update"
    ],
    "data" : [
        "wizard/export_modelo303_to_boe.xml",
        # "wizard/wizard_chart_update_view.xml",
        "modelo303_view.xml",
        "modelo303_casillas.xml",
        "security/ir.model.access.csv",
    ],
    "installable" : True,
    "post_init_hook" : "mod303_post_init_hook",
}
