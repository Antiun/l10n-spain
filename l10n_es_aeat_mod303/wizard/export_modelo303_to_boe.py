# -*- encoding: utf-8 -*-
##############################################################################
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
from datetime import datetime
import base64
import time

from openerp.tools.translate import _
from openerp.osv import orm
from openerp.tools.safe_eval import safe_eval


class l10n_es_aeat_modelo303_export_to_boe(orm.TransientModel):
    _inherit = "l10n.es.aeat.report.export_to_boe"
    _name = 'l10n.es.aeat.modelo303.export_to_boe'

    def _validate_template_line(self, template_line):
        # TODO: Validar formato de las lineas de la plantilla del 303
        return True

    def _get_template_lines(self, report):
        template_lines = []
        template = report and report.modelo303_id and report.modelo303_id.template or ''
        for line in template.strip().split("\n"):
            line = line.strip()
            if not line or line[0] == ';':
                continue
            parts = [v.strip() for v in line.split(',')]
            tmpl_line = {"long": parts[0], 
                         "longdec": parts[1],
                         "tipo_formato": parts[2],
                         "valor": parts[3]}
            self._validate_template_line(tmpl_line)
            template_lines.append(tmpl_line)
        return template_lines

    def _get_formatted_declaration_record(self, cr, uid, report, context=None):
        return ''

    def _get_formatted_main_record(self, cr, uid, report, context=None):
        ccc_devolucion = ""
        ccc_devolucion_iban = ""
        if report.cuenta_devolucion_id:
            ccc_devolucion = report.cuenta_devolucion_id.acc_number.replace("-", "").replace(" ", "")
            if len(ccc_devolucion) > 20:
                ccc_devolucion_iban = ccc_devolucion
                ccc_devolucion = ccc_devolucion[-20:]
        ccc_ingreso = ""
        ccc_ingreso_iban = ""
        if report.cuenta_ingreso_id:
            ccc_ingreso = report.cuenta_ingreso_id.acc_number.replace("-", "").replace(" ", "")
            if len(ccc_ingreso) > 20:
                ccc_ingreso_iban = ccc_ingreso
                ccc_ingreso = ccc_ingreso[-20:]
                
        date = datetime.strptime(report.calculation_date, "%Y-%m-%d %H:%M:%S")
        values = {
            'nif': report.company_vat,
            'razon_social': report.company_id.name,
            'devolucion_mensual': self._formatBoolean(report.devolucion_mensual, yes='1', no='2'),
            'ejercicio': report.fiscalyear_id.code,
            'periodo': report.period,
            'localidad': report.company_id.partner_id.city,
            'dia': date.strftime("%d"),
            'mes': _(date.strftime("%B")),
            'any': date.strftime("%Y"),
            'sin_actividad': self._formatBoolean(report.sin_actividad , yes='1', no='2'),
            'cc_devolucion_entidad': ccc_devolucion[:4],
            'cc_devolucion_oficina': ccc_devolucion[4:8],
            'cc_devolucion_dc': ccc_devolucion[8:10],
            'cc_devolucion_num':ccc_devolucion[10:],
            'cc_devolucion_iban': ccc_devolucion_iban,
            'cc_ingreso_entidad': ccc_ingreso[:4],
            'cc_ingreso_oficina': ccc_ingreso[4:8],
            'cc_ingreso_dc': ccc_ingreso[8:10],
            'cc_ingreso_num':ccc_ingreso[10:],
            'cc_ingreso_iban': ccc_ingreso_iban,
            'complementaria':  self._formatBoolean(report.complementaria, yes='1', no='2'),
            'numero_justificante': report.previous_number,
            'sujeto_a_cdc': self._formatBoolean(report.sujeto_a_cdc, yes='1', no='2'),
            'destinatario_operaciones_cdc': self._formatBoolean(report.destinatario_operaciones_cdc, yes='1', no='2'),
            'clrf': "\r\n".encode("ascii"),
        }
        casillas = {}
        for i in range(1,201):
            casillas["c%02d" % i] = 0
        for valor_casilla in report.valor_casilla_ids:
            casillas["c%s" % valor_casilla.casilla_id.code] = valor_casilla.valor

        eval_ctx = casillas.copy()
        eval_ctx.update(values)
        
        res = ''
        template_lines = self._get_template_lines(report)
        for tmpl_line in template_lines:
            valor = tmpl_line['valor']
            valor = safe_eval(valor, eval_ctx)
            
            is_neg = valor < 0
            if tmpl_line['tipo_formato'] == 'n':
                res += self._formatNumber(valor, int(tmpl_line['long']) - (is_neg and 1 or 0),
                                          int(tmpl_line['longdec']),
                                          include_sign=is_neg)
            elif tmpl_line['tipo_formato'] == 'a':
                res += self._formatString(valor, int(tmpl_line['long']))
            else:
                raise orm.except_orm("", "tipo_formato: \"%s\" debe ser uno de (a, n)")
        return res

    def _get_formatted_other_records(self, cr, uid, report, context=None):
        return ''
