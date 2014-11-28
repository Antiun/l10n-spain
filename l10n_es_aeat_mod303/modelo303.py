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
import re
from dateutil.relativedelta import relativedelta

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval
from openerp.addons.account.report.report_vat import tax_report


###### 303 templates ######

class l10n_es_aeat_modelo303_template(orm.Model):
    _name = "l10n.es.aeat.modelo303.template"
    _description = "AEAT modelo 303 template"

    _columns = {
        'name': fields.char('Nombre', size=256, required=True),
        'date': fields.date("Fecha entrada en vigor"),
        'template': fields.text('Template', readonly=True)
    }

l10n_es_aeat_modelo303_template()

class l10n_es_aeat_modelo303_casilla_template(orm.Model):
    _name = "l10n.es.aeat.modelo303.casilla.template"
    _description = "Casillas AEAT modelo 303 template"

    _columns = {
        'modelo303_id': fields.many2one('l10n.es.aeat.modelo303.template', 'Modelo 303', required=True, select=True),
        'name': fields.char('Nombre', size=256, required=True),
        'code': fields.char('Casilla', size=16, required=True),
        'tax_code_ids': fields.many2many('account.tax.code.template', 'rel_casilla_tax_codes_template', 'casilla_template_id', 'tax_code_template_id'),
        'evaluate_as': fields.char("Evaluar como", 128, required=False),
        'default_value': fields.float("Valor por defecto", required=False),
    }

    _defaults = {
        'evaluate_as': '',
    }

    _sql_constraints = [('casillas_aeat_code_fiscalyear_unique', 'unique(code, modelo303_id)', 'Las casillas deben ser unicas por modelo.')]

l10n_es_aeat_modelo303_casilla_template()

###### 303 objects #######

class l10n_es_aeat_modelo303(orm.Model):
    _name = "l10n.es.aeat.modelo303"
    _description = "AEAT modelo 303"

    _columns = {
        'name': fields.char('Nombre', size=256, required=True),
        'date': fields.date("Fecha entrada en vigor"),
        'template': fields.text('Template', readonly=True)
    }

l10n_es_aeat_modelo303()

class l10n_es_aeat_modelo303_casilla(orm.Model):
    _name = "l10n.es.aeat.modelo303.casilla"
    _description = "Casillas AEAT modelo 303"

    _columns = {
        'modelo303_id': fields.many2one('l10n.es.aeat.modelo303', 'Modelo 303', required=True, select=True),
        'name': fields.char('Nombre', size=256, required=True),
        'code': fields.char('Casilla', size=16, required=True),
        'tax_code_ids': fields.many2many('account.tax.code', 'rel_casilla_tax_codes', 'casilla_id', 'tax_code_id'),
        'evaluate_as': fields.char("Evaluar como", 128, required=False),
        'default_value': fields.float("Valor por defecto", required=False),
    }

    _defaults = {
        'evaluate_as': '',
    }

    _sql_constraints = [('casillas_aeat_code_fiscalyear_unique', 'unique(code, modelo303_id)', 'Las casillas deben ser unicas por modelo.')]

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','code', 'evaluate_as'], context, load='_classic_write')
        return [(x['id'], x['name'] + (x['evaluate_as'] and (" [" + x['evaluate_as'] + ']') or '')) \
               for x in reads]

    def get_dependency_codes(self, cr, uid, ids, context=None):
        result = {}
        casilla_code_re = re.compile("c([0-9a-zA-Z]+)")
        for casilla in self.browse(cr, uid, ids, context):
            dep_codes = []
            if casilla.evaluate_as:
                dep_codes = casilla_code_re.findall(casilla.evaluate_as)
            result[casilla.id] = dep_codes
        return result

l10n_es_aeat_modelo303_casilla()

class l10n_es_aeat_modelo303_valor_casilla(orm.Model):
    _name = "l10n.es.aeat.modelo303.valor.casilla"
    _description = "AEAT modelo 303 valor casilla"
    _order = 'code asc'

    _columns = {
        'report_id': fields.many2one("l10n.es.aeat.modelo303.report", "Report", required=True),
        'casilla_id': fields.many2one("l10n.es.aeat.modelo303.casilla", "Casilla", required=True), # 1-1
        'code': fields.char('Casilla', size=16, required=True),
        'valor': fields.float("Valor"),
    }
    _sql_constraints = [('aeat_modelo303_report_casilla_unique', 'unique(report_id, casilla_id)',
                         'Una casilla solo puede tener un valor')]

l10n_es_aeat_modelo303_valor_casilla()


class l10n_es_aeat_modelo303_report(orm.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.modelo303.report"
    _description = "AEAT modelo 303 report"

    def _get_fiscalyear_id(self, cr, uid, context=None):
        fiscalyear_obj = self.pool.get("account.fiscalyear")
        today = datetime.today().date()
        return fiscalyear_obj.search(cr, uid,
                                     ['&', ('date_start', '<=', today),
                                      ('date_stop', '>=', today)])[0] or False


    def _get_modelo303_id(self, cr, uid, context=None):
        modelo303_obj = self.pool.get("l10n.es.aeat.modelo303")
        fiscalyear_obj = self.pool.get("account.fiscalyear")

        mod303_id = None
        mod303_date = None
        fiscalyear_ids = self._get_fiscalyear_id(cr, uid, context)
        if fiscalyear_ids:
            fiscalyear = fiscalyear_obj.browse(cr, uid, fiscalyear_ids)
            mod303_ids = modelo303_obj.search(cr, uid,
                                              [('date', '<=', fiscalyear.date_start)])
            if mod303_ids:
                for m303 in modelo303_obj.browse(cr, uid, mod303_ids):
                    if not mod303_date or m303.date >= mod303_date:
                        mod303_id = m303.id
                        mod303_date = m303.date

        return mod303_id or False

    def _get_period(self, cr, uid, ids, context=None):
        period_obj = self.pool.get("account.period")
        account_period_id = []
        for mod303 in self.browse(cr, uid, ids, context=context):
            account_period_id.append(mod303.period_start_id.id)
            if mod303.period_end_id:
                if mod303.period_start_id.date_start > mod303.period_end_id.date_start:
                    raise orm.except_orm('', _('El periodo inicial debe ser inferior o igual periodo final.'))

                if mod303.period_start_id.id <> mod303.period_end_id.id:
                    account_period_id.append(mod303.period_end_id.id)
                    account_period_id += period_obj.search(cr, uid,
                                [('date_start', '>', mod303.period_start_id.date_stop),
                                 ('date_stop', '<', mod303.period_end_id.date_start),
                                 ('id', 'not in', account_period_id),
                                 ('special', '=', False),],
                                context=context)
        return account_period_id

    def _get_valores_casillas(self, cr, uid, ids, modelo303_id, default_values=None, context=None):
        if default_values == None:
            default_values = {}
        casillas_obj = self.pool.get('l10n.es.aeat.modelo303.casilla')
        tax_code_obj = self.pool.get('account.tax.code')
        casillas = {}
        periodos = self._get_period(cr, uid, ids, context)
        casillas_ids = casillas_obj.search(cr, uid,
                                           [('modelo303_id', '=', modelo303_id)],
                                           context=context)

        # Calculamos el valor de las casillas desde los impuestos
        for c in casillas_obj.browse(cr, uid, casillas_ids):
            if c.code in default_values:
                casillas[c.code] = default_values[c.code]
            else:
                casillas[c.code] = 0.0
                for tax_code in c.tax_code_ids:
                    for periodo in periodos:
                        ctx = {'period_id': periodo}
                        tax_code_period_sum = tax_code_obj._sum_period(cr, uid, [tax_code.id], '', {}, context=ctx)
                        casillas[c.code] += tax_code_period_sum[tax_code.id]

        # Calculamos el valor de las casillas con formulas
        for c in casillas_obj.browse(cr, uid, casillas_ids):
            if c.evaluate_as:
                self._calcular_casilla(cr, uid, modelo303_id, c.code, casillas, default_values, context)

        return casillas

    def _calcular_casilla(self, cr, uid, modelo303_id, code, valores_casillas, default_values=None, context=None):

        if default_values == None:
            default_values = {}

        casillas_obj = self.pool.get('l10n.es.aeat.modelo303.casilla')
        casillas_id = casillas_obj.search(cr, uid, [('modelo303_id', '=', modelo303_id),
                                                   ('code', '=', code)])
        if not casillas_id:
            valores_casillas[code] = 0.0
        else:
            casilla = casillas_obj.browse(cr, uid, casillas_id)[0]
            if casilla and casilla.evaluate_as:
                dep_codes = casillas_obj.get_dependency_codes(cr, uid, [casilla.id])[casilla.id]
                for dep_code in dep_codes:
                    if dep_code not in valores_casillas or valores_casillas[dep_code] == 0 and dep_code != code:
                        self._calcular_casilla(cr, uid, modelo303_id, dep_code, valores_casillas, default_values, context)

                if casilla.code in default_values:
                    valores_casillas[casilla.code] = default_values[casilla.code]
                else:
                    eval_ctx = {}
                    for k, v in valores_casillas.iteritems():
                         eval_ctx['c%s' % k] = v
                    valores_casillas[casilla.code] = safe_eval(casilla.evaluate_as, eval_ctx)

    _columns = {
        'company_partner_id': fields.related('company_id', 'partner_id',
                type='many2one', relation='res.partner', string='Partner',
                store=True),
        'period': fields.selection(
                [('1T', 'First quarter'), ('2T', 'Second quarter'),
                 ('3T', 'Third quarter'), ('4T', 'Fourth quarter'),
                 ('01', 'January'), ('02', 'February'), ('03', 'March'),
                 ('04', 'April'), ('05', 'May'), ('06', 'June'),
                 ('07', 'July'), ('08', 'August'), ('09', 'September'),
                 ('10', 'October'), ('11', 'November'), ('12', 'December')],
                'Period', states={'done':[('readonly',True)]}),
        'period_start_id': fields.many2one("account.period", 'Period start', states={'done':[('readonly',True)]}),
        'period_end_id': fields.many2one("account.period", 'Period end', states={'done':[('readonly',True)]}),
        'devolucion_mensual': fields.boolean("Devolución Mensual",
                help="Inscrito en el Registro de Devolución Mensual",
                states={'done':[('readonly',True)]}),
        'sujeto_a_cdc': fields.boolean("Sujeto a criterio de caja",
                help="¿Ha optado por el régimen especial del criterio de Caja (art. 163 undecies LIVA)?",
                states={'done':[('readonly',True)]}),
        'destinatario_operaciones_cdc': fields.boolean("Destinatario de operaciones con criterio de caja",
                help="¿Es destinatario de operaciones a las que se aplique el régimen especial del criterio de caja?",
                states={'done':[('readonly',True)]}),
        'complementaria': fields.boolean("Autoliquidación complementaria",
                states={'done':[('readonly',True)]}),
        'cuenta_devolucion_id': fields.many2one("res.partner.bank",
                "CCC devolución", states={'done':[('readonly',True)]}),
        'cuenta_ingreso_id': fields.many2one("res.partner.bank",
                "CCC Ingreso", states={'done':[('readonly',True)]}),
        'sin_actividad': fields.boolean("Sin actividad",
                                        states={'done':[('readonly',True)]}),
        'valor_casilla_ids': fields.one2many("l10n.es.aeat.modelo303.valor.casilla", "report_id", "Valores Casillas",
                                        states={'done':[('readonly',True)]}), # 1-1
        'modelo303_id': fields.many2one("l10n.es.aeat.modelo303", "Modelo 303",
                                        states={'done':[('readonly',True)]}),
    }

    _defaults = {
        'number' : '303',
        'fiscalyear_id': _get_fiscalyear_id,
        'modelo303_id': _get_modelo303_id
    }


    def calculate(self, cr, uid, ids, context=None):
        casilla_obj = self.pool.get('l10n.es.aeat.modelo303.casilla')
        valor_casilla_obj = self.pool.get('l10n.es.aeat.modelo303.valor.casilla')
        for report303 in self.browse(cr, uid, ids, context=context):

            # Eliminamos los valores anteriores
            valor_casillas_ids = [valor_casilla.id for valor_casilla in report303.valor_casilla_ids]
            if valor_casillas_ids:
                valor_casilla_obj.unlink(cr, uid, valor_casillas_ids)

            # Valores por defecto
            default_values = {}
            casilla_ids = casilla_obj.search(cr, uid, [('modelo303_id','=', report303.modelo303_id.id)])
            for c in casilla_obj.browse(cr, uid, casilla_ids):
                if c.default_value and not c.tax_code_ids and not c.evaluate_as:
                    default_values[c.code] = c.default_value

            valores_casillas = self._get_valores_casillas(cr, uid, ids,
                                                          report303.modelo303_id.id,
                                                          default_values=default_values,
                                                          context=context)
            for casilla_code in valores_casillas.keys():
                casilla_ids = casilla_obj.search(cr, uid, # TODO: *1 optimizar esto...
                                                 [('code', '=', casilla_code),
                                                  ('modelo303_id','=',
                                                   report303.modelo303_id.id)])
                if casilla_ids:
                    valor_casilla = {
                        'valor': valores_casillas[casilla_code],
                        'code': casilla_code,
                        'casilla_id': casilla_ids[0], # TODO: *1 optimizar esto...
                        'report_id': report303.id,
                    }
                    valor_casilla_obj.create(cr, uid, valor_casilla)
        return True

    def button_calculate_formulas(self, cr, uid, ids, context=None):
        valor_casilla_obj = self.pool.get('l10n.es.aeat.modelo303.valor.casilla')
        for report303 in self.browse(cr, uid, ids, context=context):

            default_values = {}
            for casilla_valor in report303.valor_casilla_ids:
                if not casilla_valor.casilla_id.evaluate_as:
                    default_values[casilla_valor.code] = casilla_valor.valor
            valores_casillas = self._get_valores_casillas(cr, uid, ids,
                                                          report303.modelo303_id.id,
                                                          default_values=default_values,
                                                          context=context)
            for casilla_valor in report303.valor_casilla_ids:
                if casilla_valor.casilla_id.evaluate_as:
                    value = {'valor': valores_casillas[casilla_valor.code]}
                    valor_casilla_obj.write(cr, uid, [casilla_valor.id], value)

        return True

    def button_confirm(self, cr, uid, ids, context=None):
        """Check its records"""
        msg = ""
        for modelo303 in self.browse(cr, uid, ids, context=context):
            if modelo303.devolucion_mensual and modelo303.period in ('1T', '2T', '3T', '4T'):
                msg = _('Inscrito en el Registro de devolución mensual (Art. 30 RIVA). No está permitido para periodos 1T,2T,3T o 4T.')
        if msg:
            raise orm.except_orm("", msg)
        return super(l10n_es_aeat_modelo303_report, self).button_confirm(cr, uid,
                                                        ids, context=context)

